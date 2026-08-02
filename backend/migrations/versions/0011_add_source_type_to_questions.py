"""Add source_type column to questions table

Revision ID: 0011_add_source_type_to_questions
Revises: 0010_add_yearly_billing_period
Create Date: 2026-07-10 00:00:00.000000

Adds a source_type column to the questions table so we can distinguish
questions that were extracted from previous year papers ('question_paper')
vs questions generated from textbook content ('textbook').
"""
from alembic import op
import sqlalchemy as sa

revision = '0011_add_source_type_to_questions'
down_revision = '0010_add_yearly_billing_period'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect as sa_inspect
    from alembic import context
    bind = context.get_bind()
    insp = sa_inspect(bind)
    existing_cols = [c['name'] for c in insp.get_columns('questions')]

    if 'source_type' not in existing_cols:
        with op.batch_alter_table('questions', schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    'source_type',
                    sa.String(20),
                    nullable=False,
                    server_default='question_paper',
                )
            )


def downgrade():
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_column('source_type')
