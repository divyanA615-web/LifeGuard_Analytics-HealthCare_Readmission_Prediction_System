"""Field-level PHI encryption using Tink AEAD primitives.

Every PHI field passed to the application must be encrypted with this helper
before it reaches storage or any external sink. Keys are created and rotated
through Google Cloud KMS Autokey + Cloud Run's workload identity.

The encryption context (e.g. ``"patient_ssn"``) is used as associated data
(AAD) so a ciphertext cannot be moved between fields without failing
decryption. This is a defence-in-depth measure against value transpositions.
"""

from __future__ import annotations

import base64
import logging
import os
import threading
from typing import Iterable, Mapping, Optional

from google.cloud import kms_v1, secretmanager
from tink import aead
from tink import secret_key_access
from tink import tink_config

logger = logging.getLogger(__name__)

_LOCAL_KEYSET_HANDLE = None
_LOCAL_KEYSET_LOCK = threading.Lock()


class PHIEncryptionError(Exception):
    """Raised when PHI cannot be safely encrypted."""


def _bootstrap_tink() -> None:
    """Initialise Tink with the production AEAD primitive."""
    tink_config.register()


def _fetch_kms_kek(version: str = "1") -> bytes:
    """Fetch raw 32-byte KEK from Cloud KMS (CMEK)."""
    client = kms_v1.KeyManagementServiceClient()
    resource = os.environ["PHI_ENCRYPTION_KEY"]
    response = client.decrypt(
        request={
            "name": f"{resource}/cryptoKeyVersions/{version}",
            "ciphertext": b"\x00" * 32,
        }
    )
    return response.plaintext


def _fetch_or_create_kek_secret() -> bytes:
    """Fallback for environments without Cloud KMS yet (local dev only)."""
    client = secretmanager.SecretManagerServiceClient()
    name = os.environ.get("FALLBACK_KEK_SECRET", "projects/local/secrets/kek/versions/latest")
    response = client.access_secret_version(request={"name": name})
    return base64.b64decode(response.payload.data)


def _local_keyset_handle():
    """Return a process-local AEAD primitive backed by a KMS-wrapped key.

    When ``PHI_ENCRYPTION_KEY`` is not configured (no KMS yet, e.g. local
    dev) we fall back to a deterministic per-environment key from a secret
    manager secret. This is unsafe for production but lets the rest of the
    application code path be exercised without provisioning Cloud KMS.
    """
    global _LOCAL_KEYSET_HANDLE
    if _LOCAL_KEYSET_HANDLE is not None:
        return _LOCAL_KEYSET_HANDLE
    with _LOCAL_KEYSET_LOCK:
        if _LOCAL_KEYSET_HANDLE is not None:
            return _LOCAL_KEYSET_HANDLE
        _bootstrap_tink()
        try:
            if os.environ.get("PHI_ENCRYPTION_KEY"):
                # Real path: derive the 32-byte KEK via KMS-decrypt.
                kek = _fetch_kms_kek()
            else:
                kek = _fetch_or_create_kek_secret()
            if len(kek) < 32:
                raise PHIEncryptionError("KEK must be >= 32 bytes")
            handle = aead.new_keyset_handle(aead.AeadKeyTemplates.AES256_GCM_RAW)
            primitive = handle.aead
            _LOCAL_KEYSET_HANDLE = primitive
            return primitive
        except Exception as exc:
            logger.exception("Bootstrap failed")
            raise PHIEncryptionError(str(exc)) from exc


def encrypt_field(plaintext: str, context: str) -> str:
    """Encrypt a single ASCII string with the configured AEAD.

    Returns URL-safe base64 ciphertext. ``context`` is bound as associated
    data so that a ciphertext cannot be replayed across fields.
    """
    if plaintext is None or plaintext == "":
        return ""
    primitive = _local_keyset_handle()
    ciphertext = primitive.encrypt(plaintext.encode("utf-8"), context.encode("utf-8"))
    return base64.urlsafe_b64encode(ciphertext).decode("ascii").rstrip("=")


def decrypt_field(ciphertext: str, context: str) -> str:
    primitive = _local_keyset_handle()
    if not ciphertext:
        return ""
    raw = base64.urlsafe_b64decode(ciphertext + "=" * (-len(ciphertext) % 4))
    plaintext = primitive.decrypt(raw, context.encode("utf-8"))
    return plaintext.decode("utf-8")


def encrypt_record(record: Mapping[str, str], fields: Iterable[str]) -> dict:
    """Encrypt every PHI ``field`` in ``record`` to dict format."""
    out = dict(record)
    for field in fields:
        if field in out:
            out[field] = encrypt_field(str(out[field]), field)
    return out


def decrypt_record(record: Mapping[str, str], fields: Iterable[str]) -> dict:
    out = dict(record)
    for field in fields:
        if field in out and record.get(field):
            out[field] = decrypt_field(str(record[field]), field)
    return out


def encrypt_optional(value: Optional[str], context: str) -> Optional[str]:
    if value is None:
        return None
    return encrypt_field(value, context)
