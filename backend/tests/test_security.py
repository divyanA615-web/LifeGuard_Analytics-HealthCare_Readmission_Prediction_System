"""Security-critical tests: encrypt/decrypt + deidentification gate."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.security.phi_encryptor import encrypt_field, decrypt_field  # noqa
from app.security.deid_gate import DeIdentificationGate, TokenMap, PHILeakError  # noqa


def test_roundtrip_phi_encryption(monkeypatch) -> None:
    monkeypatch.setenv("FALLBACK_KEK_SECRET", "test-secret-not-secure")
    monkeypatch.setenv("PHI_ENCRYPTION_KEY", "")
    import importlib
    import app.security.phi_encryptor as enc
    importlib.reload(enc)

    secret = "patient-ssn-123-45-6789"
    ciphertext = enc.encrypt_field(secret, "ssn")
    assert ciphertext and ciphertext != secret
    assert enc.decrypt_field(ciphertext, "ssn") == secret


def test_deidentification_removes_phi(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test")
    gate = DeIdentificationGate(project_id="test")

    payload = {
        "patient_name": "John Smith",
        "mrn": "1234567",
        "ssn": "123-45-6789",
        "context_text": "Patient John was admitted on 2024-01-01 with chest pain",
    }
    scrubbed, tokens = gate.prepare_payload(payload)
    assert "John Smith" not in str(scrubbed)
    assert "123-45-6789" not in str(scrubbed)
    assert any(s.startswith("ssn=") for s in str(scrubbed))


def test_token_map_round_trip() -> None:
    tm = TokenMap()
    tm.token_for("John Smith", "v1")
    assert len(tm._store) == 1
