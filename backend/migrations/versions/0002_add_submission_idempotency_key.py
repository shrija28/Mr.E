"""add submission idempotency_key

Adds a nullable ``idempotency_key`` column to ``submissions`` plus a
unique constraint on ``(user_id, idempotency_key)`` so retried POSTs to
``/api/student/submit`` don't create duplicate rows.

Both SQLite and PostgreSQL treat NULL values as distinct in a UNIQUE
constraint, so existing rows (with a NULL ``idempotency_key``) coexist
with new rows that carry a non-null token.

Revision ID: 0002_add_submission_idempotency_key
Revises: 0001_initial_schema
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_add_submission_idempotency_key"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ``batch_alter_table`` is required for SQLite (which doesn't support
    # ALTER TABLE ADD CONSTRAINT) and harmless on PostgreSQL.
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.add_column(
            sa.Column("idempotency_key", sa.String(length=64), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_submissions_user_idempotency_key",
            ["user_id", "idempotency_key"],
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table("submissions") as batch_op:
        batch_op.drop_constraint(
            "uq_submissions_user_idempotency_key", type_="unique"
        )
        batch_op.drop_column("idempotency_key")
