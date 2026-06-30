"""Database models for the readmissions platform.

This module re-exports plaintext SQLAlchemy ORM models; the column-level
encryption is applied via application logic (the ``phi_encryptor``) and
the audit chain at insert time. PHI fields are stored as bytes / strings
of ciphertext; the application decrypts them only after re-authenticating.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Patient(Base):
    """De-identified patient record. No PHI stored unencrypted.

    PHI fields (ssn, mrn, name, dob) are stored as ciphertext strings produced
    by ``phi_encryptor.encrypt_field``.
    """

    __tablename__ = "patients"

    id = Column(BigInteger, primary_key=True)
    patient_token = Column(String(64), unique=True, index=True, nullable=False)
    ssn_enc = Column(Text)
    mrn_enc = Column(Text)
    name_enc = Column(Text)
    dob_enc = Column(Text)
    age_band = Column(String(8))
    gender = Column(String(8))
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class Prediction(Base):
    """A single scoring event."""

    __tablename__ = "predictions"

    id = Column(BigInteger, primary_key=True)
    patient_token = Column(String(64), index=True, nullable=False)
    model_version = Column(String(32), nullable=False)
    risk_proba = Column(Float, nullable=False)
    risk_label = Column(String(16), nullable=False)
    features_json = Column(JSON, nullable=False)
    explanation_json = Column(JSON, nullable=False)
    clinician_id = Column(String(64), nullable=False)
    actor_email = Column(String(120))
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False, index=True)
    feedback_at = Column(DateTime)


class AuditEntry(Base):
    """Append-only audit trail.

    The ``AuditLogger`` writes to ndjson; this table mirrors a structured
    version of the same data for partitioned long-term storage.
    """

    __tablename__ = "audit_entries"

    id = Column(BigInteger, primary_key=True)
    actor = Column(String(120), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    target = Column(String(120), nullable=False)
    payload_json = Column(JSON, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    chain_hash = Column(String(64), nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False, index=True)


class Feedback(Base):
    """Clinicians' post-prediction feedback used to retrain the model."""

    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True)
    prediction_id = Column(BigInteger, index=True, nullable=False)
    clinician_id = Column(String(64), index=True, nullable=False)
    actual_readmitted_30d = Column(Boolean, nullable=False)
    clinician_notes_enc = Column(Text)
    submitted_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


class PatientEmbedding(Base):
    """pgvector column storing patient similarity vectors.

    For local dev we use ``JSON`` so SQLite + unit tests still work; in prod
    we switch to a VECTOR column managed by Cloud SQL's pgvector extension.
    """

    __tablename__ = "patient_embeddings"

    id = Column(BigInteger, primary_key=True)
    patient_token = Column(String(64), unique=True, index=True, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
