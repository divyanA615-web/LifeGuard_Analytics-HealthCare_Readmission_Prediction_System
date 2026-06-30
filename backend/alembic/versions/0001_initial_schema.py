-- Initial schema migration applied automatically by Alembic.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pgvector;

CREATE TABLE patients (
    id BIGSERIAL PRIMARY KEY,
    patient_token VARCHAR(64) UNIQUE NOT NULL,
    ssn_enc TEXT,
    mrn_enc TEXT,
    name_enc TEXT,
    dob_enc TEXT,
    age_band VARCHAR(8),
    gender VARCHAR(8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE predictions (
    id BIGSERIAL PRIMARY KEY,
    patient_token VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    risk_proba FLOAT NOT NULL,
    risk_label VARCHAR(16) NOT NULL,
    features_json JSONB NOT NULL,
    explanation_json JSONB NOT NULL,
    clinician_id VARCHAR(64) NOT NULL,
    actor_email VARCHAR(120),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    feedback_at TIMESTAMP
);

CREATE INDEX ix_predictions_patient ON predictions (patient_token);
CREATE INDEX ix_predictions_created_at ON predictions (created_at DESC);

CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT NOT NULL,
    clinician_id VARCHAR(64) NOT NULL,
    actual_readmitted_30d BOOLEAN NOT NULL,
    clinician_notes_enc TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE audit_entries (
    id BIGSERIAL PRIMARY KEY,
    actor VARCHAR(120) NOT NULL,
    action VARCHAR(64) NOT NULL,
    target VARCHAR(120) NOT NULL,
    payload_json JSONB NOT NULL,
    prev_hash VARCHAR(64) NOT NULL,
    chain_hash VARCHAR(64) NOT NULL,
    occurred_at TIMESTAMP NOT NULL
);

CREATE INDEX ix_audit_actor ON audit_entries (actor);
CREATE INDEX ix_audit_chain ON audit_entries (chain_hash);

CREATE UNIQUE INDEX ix_audit_chain_unique ON audit_entries (chain_hash);
