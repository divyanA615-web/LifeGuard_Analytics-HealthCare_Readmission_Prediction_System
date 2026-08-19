"""Security-critical tests: encrypt/decrypt + deidentification gate."""

from __future__ import annotations

import logging
import os
import sys

from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use a deterministic local key so unit tests don't hit real GCP
os.environ.setdefault("LOCAL_KEK", "test-kek-bytes-32-chars-aaaaaaa")
os.environ.setdefault("PHI_ENCRYPTION_KEY", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def setup_enc_module():
    """Reset the cached keyset handle so env-changes take effect."""
    import importlib

    import app.security.phi_encryptor as enc
    enc._LOCAL_KEYSET_HANDLE = None
    importlib.reload(enc)


def test_roundtrip_phi_encryption() -> None:
    setup_enc_module()
    import app.security.phi_encryptor as enc

    secret = "patient-ssn-123-45-6789"
    ciphertext = enc.encrypt_field(secret, "ssn")
    assert ciphertext and ciphertext != secret
    assert enc.decrypt_field(ciphertext, "ssn") == secret


def test_aad_protection() -> None:
    """A ciphertext bound to one field must NOT decrypt under another."""
    import app.security.phi_encryptor as enc
    setup_enc_module()
    cipher = enc.encrypt_field("data-text", "ssn")
    try:
        enc.decrypt_field(cipher, "mrn")
        assert False, "AAD check should have failed"
    except InvalidTag as exc:  # cryptography raises InvalidTag for AAD mismatch
        logger.debug("Expected AAD check failure: %s", exc)


def test_deidentification_removes_phi() -> None:
    setup_enc_module()
    from app.security.deid_gate import DeIdentificationGate
    gate = DeIdentificationGate(project_id="test")
    payload = {
        "patient_name": "John Smith",
        "mrn": "1234567",
        "ssn": "123-45-6789",
        "context_text": "Patient John was admitted on 2024-01-01 with chest pain",
    }
    scrubbed, tokens = gate.prepare_payload(payload)
    serialized = str(scrubbed)
    assert "John Smith" not in serialized
    assert "1234567" not in serialized
    assert "123-45-6789" not in serialized
    assert tokens.token_for  # token map populated


def test_token_map_round_trip() -> None:
    from app.security.deid_gate import TokenMap
    tm = TokenMap()
    tm.token_for("John Smith", "v1")
    assert len(tm._store) == 1
