"""Initial schema: patients, predictions, feedback, audit chain.

Revision ID: 0001
Revises:
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Extensions (only enable pgcrypto which ships with alpine postgres)
    try:
        bind.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    except Exception as exc:  # noqa: BLE001
        print(f"[alembic] extension skipped: pgcrypto -> {exc}")

    # pgvector deliberately skipped — not needed for baseline feature tracking.

    # Patients
    op.create_table(
        'patients',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('patient_token', sa.String(64), nullable=False, unique=True),
        sa.Column('ssn_enc', sa.Text()),
        sa.Column('mrn_enc', sa.Text()),
        sa.Column('name_enc', sa.Text()),
        sa.Column('dob_enc', sa.Text()),
        sa.Column('age_band', sa.String(8), nullable=False),
        sa.Column('gender', sa.String(8), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )

    # Predictions
    op.create_table(
        'predictions',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('patient_token', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('risk_proba', sa.Numeric(10, 6), nullable=False),
        sa.Column('risk_label', sa.String(16), nullable=False),
        sa.Column('features_json', sa.JSON(), nullable=False),
        sa.Column('explanation_json', sa.JSON(), nullable=False),
        sa.Column('clinician_id', sa.String(64), nullable=False),
        sa.Column('actor_email', sa.String(120)),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('feedback_at', sa.TIMESTAMP()),
    )
    op.create_index('ix_predictions_patient', 'predictions', ['patient_token'])
    op.create_index('ix_predictions_created_at', 'predictions', [sa.text('created_at DESC')])

    # Feedback
    op.create_table(
        'feedback',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('prediction_id', sa.BigInteger(), sa.ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clinician_id', sa.String(64), nullable=False),
        sa.Column('actual_readmitted_30d', sa.Boolean(), nullable=False),
        sa.Column('clinician_notes_enc', sa.Text()),
        sa.Column('submitted_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )

    # Audit entries (hash-chained)
    op.create_table(
        'audit_entries',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('target', sa.String(120), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('prev_hash', sa.String(64), nullable=False),
        sa.Column('chain_hash', sa.String(64), nullable=False),
        sa.Column('occurred_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_audit_actor', 'audit_entries', ['actor'])
    op.create_index('ix_audit_chain', 'audit_entries', ['chain_hash'])
    op.create_index('ix_audit_chain_unique', 'audit_entries', ['chain_hash'], unique=True)


def downgrade() -> None:
    op.drop_table('feedback')
    op.drop_table('predictions')
    op.drop_table('patients')
    op.drop_table('audit_entries')
