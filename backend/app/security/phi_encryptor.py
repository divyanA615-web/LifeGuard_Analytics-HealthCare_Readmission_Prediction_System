"""Field-level PHI encryption using AES-256-GCM via the cryptography library.

Every PHI field passed to the application is encrypted with AES-256-GCM
before it touches storage or any external sink. Keys are managed by
Cloud KMS in production; tests fall back to a deterministic local key
(see ``LOCAL_KEK`` env).

The encryption context (e.g. ``"patient_ssn"``) is bound as associated
data (AAD) so a ciphertext cannot be moved between fields without
failing decryption. This defends against value transpositions.
"""

from __future__ import annotations

import base64
import logging
import os
import threading
from collections.abc import Iterable, Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

_LOCAL_AES = None
_LOCAL_AES_LOCK = threading.Lock()
_NONCE_LEN = 12  # AES-GCM nonce length


class PHIEncryptionError(Exception):
    """Raised when PHI cannot be safely encrypted."""


def _local_key() -> bytes:
    """Return a 32-byte AES key.

    Production: comes from Cloud KMS via ``PHI_ENCRYPTION_KEY``.
    Local dev / tests: from ``LOCAL_KEK`` env var (padded to 32 bytes).
    """
    if os.environ.get("PHI_ENCRYPTION_KEY"):
        # Production: fetch the key from Cloud KMS Autokey.
        from google.cloud import kms_v1

        client = kms_v1.KeyManagementServiceClient()
        resource = os.environ["PHI_ENCRYPTION_KEY"]
        response = client.decrypt(
            request={
                "name": f"{resource}/cryptoKeyVersions/1",
                "ciphertext": b"\x00" * 32,
            }
        )
        return response.plaintext[:32]

    local = os.environ.get("LOCAL_KEK")
    if not local:
        raise PHIEncryptionError("LOCAL_KEK env var is not set")
    if len(local) >= 32:
        return local.encode("utf-8")[:32]
    return (local * (32 // len(local) + 1))[:32].encode("utf-8")


def _local_primitive() -> AESGCM:
    """Return a process-local AESGCM primitive."""
    global _LOCAL_AES
    if _LOCAL_AES is not None:
        return _LOCAL_AES
    with _LOCAL_AES_LOCK:
        if _LOCAL_AES is not None:
            return _LOCAL_AES
        try:
            key = _local_key()
            if len(key) != 32:
                raise PHIEncryptionError(f"key length {len(key)} != 32")
            _LOCAL_AES = AESGCM(key)
            return _LOCAL_AES
        except Exception as exc:
            logger.exception("Bootstrap failed")
            raise PHIEncryptionError(str(exc)) from exc


def encrypt_field(plaintext: str, context: str) -> str:
    """Encrypt a single ASCII string with the configured AES-256-GCM.

    Returns URL-safe base64 ciphertext. ``context`` is bound as
    associated data so a ciphertext cannot be replayed across fields.
    """
    if plaintext is None or plaintext == "":
        return ""
    aes = _local_primitive()
    nonce = os.urandom(_NONCE_LEN)
    cipher = aes.encrypt(nonce, plaintext.encode("utf-8"), context.encode("utf-8"))
    return base64.urlsafe_b64encode(nonce + cipher).decode("ascii").rstrip("=")


def decrypt_field(ciphertext: str, context: str) -> str:
    if not ciphertext:
        return ""
    raw = base64.urlsafe_b64decode(ciphertext + "=" * (-len(ciphertext) % 4))
    nonce, body = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
    aes = _local_primitive()
    plaintext = aes.decrypt(nonce, body, context.encode("utf-8"))
    return plaintext.decode("utf-8")


def encrypt_record(record: Mapping[str, str], fields: Iterable[str]) -> dict:
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


def encrypt_optional(value: str | None, context: str) -> str | None:
    if value is None:
        return None
    return encrypt_field(value, context)
