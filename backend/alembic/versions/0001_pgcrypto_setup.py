"""SQL script for initial schema generation. Used by Alembic migrations."""

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run SQL statements via op.execute()."""
    import sqlalchemy as sa
    from alembic import op

    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgvector')


def downgrade() -> None:
    pass
