"""De-identification gate.

Layer 5: every outbound payload to any NVIDIA NIM endpoint passes through this
gate, which:

1. Generates deterministic pseudonymous tokens for PHI fields.
2. Replaces PHI in the payload.
3. Sends the request to NVIDIA.
4. Optionally re-applies tokens to the response (e.g. discharge summary).

The mapping of token -> PHI lives only in the encrypted audit table; the
NVIDIA endpoint itself never sees the original PHI.

In local-dev mode (no PHI in the dataset) the gate becomes a near no-op.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from google.cloud import dlp_v2

from .phi_encryptor import encrypt_field

logger = logging.getLogger(__name__)

PHI_FIELDS = {
    "patient_name",
    "mrn",
    "ssn",
    "dob",
    "address",
    "phone",
    "email",
    "insurance_id",
    "attending_physician",
}

DLP_INFO_TYPES = [
    "PERSON_NAME",
    "US_SOCIAL_SECURITY_NUMBER",
    "DATE_OF_BIRTH",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "US_MEDICAL_RECORD_NUMBER",
    "STREET_ADDRESS",
    "US_PASSPORT",
    "IP_ADDRESS",
]

DLG_TEMPLATE_PATH = "projects/PROJECT/locations/asia-south1/deidentifyTemplates/lifeguard-lite"


@dataclass(slots=True)
class TokenMap:
    _store: dict[str, str] = field(default_factory=dict)

    def token_for(self, value: str, salt: str) -> str:
        key = f"{salt}|{value}"
        if key in self._store:
            return self._store[key]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        self._store[key] = digest
        return digest

    def reverse_map(self) -> dict[str, str]:
        return {tok: val.split("|", 1)[1] for val, tok in self._store.items()}


def _scrub_text(text: str, token_map: TokenMap, salt: str) -> str:
    """Best-effort scrub: replace obvious PHI patterns with tokens.

    Not a substitute for the Cloud DLP inspection but enough for offline usage
    where Cloud DLP isn't reachable.
    """
    patterns = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
        (r"\b\d{10}\b", "mrn"),
        (r"[A-Z][a-z]+ [A-Z][a-z]+", "patient_name"),
        (r"\b\d{4}-\d{2}-\d{2}\b", "dob"),
        (r"[\w.+-]+@[\w-]+\.[\w.-]+", "email"),
    ]
    for pattern, kind in patterns:
        re.findall(pattern, text)

        def replace(m, kind=kind):
            return f"<{kind}={token_map.token_for(m.group(), salt)}>"

        text = re.sub(pattern, replace, text)
    return text


class DeIdentificationGate:
    """High-level orchestrator for any flow that touches NVIDIA endpoints."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._dlp_client = None  # lazy create

    def _dlp(self):
        if not self._dlp_client:
            self._dlp_client = dlp_v2.DlpServiceClient()
        return self._dlp_client

    def prepare_payload(self, payload: dict[str, Any], salt: str = "v1") -> tuple[dict[str, Any], TokenMap]:
        """Create the de-identified payload for NVIDIA + an encrypted token map.

        The original payload should not be returned to the caller; only the
        scrubbed payload flows downstream.
        """
        token_map = TokenMap()
        scrubbed: dict[str, Any] = {}
        for key, value in payload.items():
            if key in PHI_FIELDS and isinstance(value, str):
                scrubbed[key] = token_map.token_for(value, salt)
            elif isinstance(value, str):
                scrubbed[key] = _scrub_text(value, token_map, salt)
            elif isinstance(value, list):
                scrubbed[key] = [
                    _scrub_text(v, token_map, salt) if isinstance(v, str) else v for v in value
                ]
            elif isinstance(value, dict):
                scrubbed[key], _ = self.prepare_payload(value, salt=salt)
            else:
                scrubbed[key] = value
        self._raise_if_phi_remains(scrubbed)
        return scrubbed, token_map

    def _raise_if_phi_remains(self, payload: dict[str, Any]) -> None:
        """Use Cloud DLP to inspect the scrubbed payload before NVIDIA."""
        try:
            client = self._dlp()
            info_types = [{"name": t} for t in DLP_INFO_TYPES]
            config = {
                "info_types": info_types,
                "min_likelihood": dlp_v2.Likelihood.LIKELY,
            }
            parent = f"projects/{self.project_id}/locations/asia-south1"
            item = {"value": str(payload).encode("utf-8")}

            response = client.inspect_content(
                request={"parent": parent, "inspect_config": config, "item": item}
            )
            if response.result.findings:
                raise PHILeakError(
                    f"{len(response.result.findings)} residual PHI token(s) detected."
                )
        except PHILeakError:
            raise
        except Exception as exc:  # pragma: no cover - DLP downstream issue
            logger.warning("Cloud DLP inspection unavailable: %s. Falling back to regex check.", exc)
            serialized = str(payload)
            for pattern in [r"\d{3}-\d{2}-\d{4}", r"[A-Z][a-z]+ [A-Z][a-z]+"]:
                if re.search(pattern, serialized):
                    raise PHILeakError("residual PHI detected after scrub") from exc

    def reattach_tokens(self, response_text: str, token_map: TokenMap) -> str:
        """Replace tokens with their original PHI in post-NVIDIA responses.

        Only invoke when the response is destined for an authenticated user
        and the original PHI is permitted by the user's role.
        """
        for token, original in token_map.reverse_map().items():
            response_text = response_text.replace(f"<{token}>", original)
        return response_text


class PHILeakError(Exception):
    """Raised when PHI is detected in an outbound payload before it leaves the
    trust boundary. Critical signal for the monitoring stack.
    """


def encrypt_token_map(token_map: TokenMap, context: str) -> dict[str, str]:
    """Persist the token -> PHI mapping in the encrypted audit table."""
    return {tok: encrypt_field(val, context) for val, tok in token_map._store.items()}
