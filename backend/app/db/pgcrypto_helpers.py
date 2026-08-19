"""pgcrypto helpers – stored-function wrappers around simmetric encrypt/decrypt.

Use ``pgp_sym_encrypt`` from inside the database to encrypt specific columns
when you want to leverage native Postgres-managed keys (for example, a key
from ``pg_authid``).
"""

from __future__ import annotations

import os

from sqlalchemy import func, text
from sqlalchemy.types import TEXT

SQL_ENABLE_PGCRYPTO = text("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def pgp_encrypt(plaintext: str, key_id: str = "pgkey-default") -> str:
    """Return a SQL expression that selects the encrypted value."""
    return func.pgp_sym_encrypt(plaintext, key_id).cast(TEXT)


def pgp_decrypt(ciphertext: str, key_id: str = "pgkey-default") -> str:
    return func.pgp_sym_decrypt(ciphertext, key_id).cast(TEXT)


def ensure_key() -> str:
    """Make sure ``PGP_KEY`` is sourced (e.g. from Secret Manager)."""
    key = os.environ.get("PGP_KEY")
    if key:
        return key
    raise RuntimeError("PGP_KEY env var is required for pgcrypto-backed columns")
