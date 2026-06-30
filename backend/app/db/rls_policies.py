"""SQL row-level security policies for the readmission platform.

Run this script once during bootstrap to install the RLS policies on
Cloud SQL. In production it should be executed via a private connection
from a Cloud Run migration job.
"""

from __future__ import annotations

from sqlalchemy import text

STATEMENTS: list[str] = [
    """CREATE EXTENSION IF NOT EXISTS pgcrypto""",
    """CREATE EXTENSION IF NOT EXISTS pgvector""",
    """ALTER TABLE predictions ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE feedback ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE audit_entries ENABLE ROW LEVEL SECURITY""",
    """CREATE OR REPLACE FUNCTION current_clinician_id() RETURNS text AS $$
        SELECT current_setting('app.clinician_id', true)
    $$ LANGUAGE SQL STABLE""",
    """DROP POLICY IF EXISTS clin_only_predictions ON predictions""",
    """CREATE POLICY clin_only_predictions ON predictions
        USING (clinician_id = current_clinician_id()
               OR current_setting('app.role', true) IN ('admin', 'compliance'))""",
    """DROP POLICY IF EXISTS clin_only_feedback ON feedback""",
    """CREATE POLICY clin_only_feedback ON feedback
        USING (clinician_id = current_clinician_id()
               OR current_setting('app.role', true) IN ('admin', 'compliance'))""",
    """DROP POLICY IF EXISTS append_only_audit ON audit_entries""",
    """CREATE POLICY append_only_audit ON audit_entries
        FOR INSERT WITH CHECK (TRUE)""",
    """CREATE POLICY append_only_audit_no_update ON audit_entries
        FOR UPDATE USING (FALSE)""",
    """CREATE POLICY append_only_audit_no_delete ON audit_entries
        FOR DELETE USING (FALSE)""",
]


def install(engine) -> None:  # pragma: no cover
    with engine.begin() as conn:
        for stmt in STATEMENTS:
            conn.execute(text(stmt))
