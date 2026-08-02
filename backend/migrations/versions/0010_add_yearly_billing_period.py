"""Add 'yearly' to subscription_plans billing_period CHECK constraint

Revision ID: 0010_add_yearly_billing_period
Revises: 0009_add_razorpay_payment_fields
Create Date: 2026-06-11 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0010_add_yearly_billing_period'
down_revision = '0009_add_razorpay_payment_fields'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER COLUMN for CHECK constraints directly.
    # batch_alter_table recreates the table, allowing the constraint change.
    with op.batch_alter_table('subscription_plans', schema=None) as batch_op:
        # Drop old constraint, recreate with 'yearly' added
        batch_op.drop_constraint('ck_subscription_plans_billing_period', type_='check')
        batch_op.create_check_constraint(
            'ck_subscription_plans_billing_period',
            "billing_period IN ('weekly', 'monthly', 'yearly')"
        )


def downgrade():
    with op.batch_alter_table('subscription_plans', schema=None) as batch_op:
        batch_op.drop_constraint('ck_subscription_plans_billing_period', type_='check')
        batch_op.create_check_constraint(
            'ck_subscription_plans_billing_period',
            "billing_period IN ('weekly', 'monthly')"
        )
