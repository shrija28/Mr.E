"""Add Razorpay payment fields to billing_records and new payment_logs table

Revision ID: 0009_add_razorpay_payment_fields
Revises: 0008_add_syllabus_topics
Create Date: 2026-06-10 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0009_add_razorpay_payment_fields'
down_revision = '0008_add_syllabus_topics'
branch_labels = None
depends_on = None


def upgrade():
    # ── Extend billing_records with Razorpay fields ──────────────────────────
    from sqlalchemy import inspect as sa_inspect
    from alembic import context
    bind = context.get_bind()
    insp = sa_inspect(bind)
    existing_cols = [c['name'] for c in insp.get_columns('billing_records')]

    if 'razorpay_order_id' not in existing_cols:
        with op.batch_alter_table('billing_records', schema=None) as batch_op:
            batch_op.add_column(sa.Column('razorpay_order_id',  sa.String(64),  nullable=True))
            batch_op.add_column(sa.Column('razorpay_payment_id', sa.String(64), nullable=True))
            batch_op.add_column(sa.Column('razorpay_signature', sa.String(256), nullable=True))
            # Override payment_method_ref length for UPI/card/netbanking descriptions
            # (already exists, just leave as-is; we add a new method_type column)
            batch_op.add_column(sa.Column('payment_method_type', sa.String(30), nullable=True))
            batch_op.add_column(sa.Column('plan_id', sa.Uuid(), nullable=True))
            batch_op.add_column(sa.Column('currency', sa.String(3), nullable=True, server_default='INR'))
            batch_op.add_column(sa.Column('amount_paise', sa.Integer(), nullable=True))

    # ── New payment_logs table — raw Razorpay event log ──────────────────────
    existing_tables = insp.get_table_names()
    if 'payment_logs' not in existing_tables:
        op.create_table(
            'payment_logs',
            sa.Column('id',             sa.Uuid(), primary_key=True),
            sa.Column('event_type',     sa.String(50),  nullable=False),
            sa.Column('razorpay_order_id',   sa.String(64), nullable=True, index=True),
            sa.Column('razorpay_payment_id', sa.String(64), nullable=True, index=True),
            sa.Column('entity_type',    sa.String(20),  nullable=True),  # 'institution' | 'user'
            sa.Column('entity_id',      sa.Uuid(),      nullable=True),
            sa.Column('subscription_id',sa.Uuid(),      nullable=True),
            sa.Column('amount_paise',   sa.Integer(),   nullable=True),
            sa.Column('currency',       sa.String(3),   nullable=True, server_default='INR'),
            sa.Column('status',         sa.String(20),  nullable=False),  # created|paid|failed|refunded
            sa.Column('raw_payload',    sa.Text(),      nullable=True),
            sa.Column('created_at',     sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        )


def downgrade():
    op.drop_table('payment_logs')
    with op.batch_alter_table('billing_records', schema=None) as batch_op:
        for col in ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
                    'payment_method_type', 'plan_id', 'currency', 'amount_paise']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
