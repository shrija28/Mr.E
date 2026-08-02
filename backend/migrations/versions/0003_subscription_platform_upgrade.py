"""subscription platform upgrade

This migration implements the subscription platform upgrade schema changes:
- Creates 7 new tables: institutions, subscription_plans, subscriptions,
  billing_records, usage_records, subscription_events, invitations
- Modifies users table: adds student_subtype and institution_id columns,
  updates role CHECK constraint to support 3 roles

The migration is separated into DDL (schema changes) and DML (data
transformations). All changes are reversible via the downgrade function.

Revision ID: 0003_subscription_platform_upgrade
Revises: 0002_add_submission_idempotency_key
Create Date: 2026-05-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0003_subscription_platform_upgrade'
down_revision: Union[str, Sequence[str], None] = '0002_add_submission_idempotency_key'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add subscription platform tables and modify users table."""
    
    # =========================================================================
    # DDL: Create new tables
    # =========================================================================
    
    # Create institutions table
    op.create_table(
        'institutions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('contact_phone', sa.String(length=15), nullable=False),
        sa.Column('subscription_status', sa.String(length=20), nullable=False, server_default='inactive'),
        sa.Column('registered_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.CheckConstraint(
            "subscription_status IN ('inactive', 'active', 'overdue', 'grace_period', 'expired')",
            name='ck_institutions_subscription_status'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('billing_period', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('max_test_attempts_per_period', sa.Integer(), nullable=True),
        sa.Column('max_student_seats', sa.Integer(), nullable=True),
        sa.Column('feature_flags', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.CheckConstraint(
            "plan_type IN ('individual', 'institution')",
            name='ck_subscription_plans_plan_type'
        ),
        sa.CheckConstraint(
            "billing_period IN ('weekly', 'monthly')",
            name='ck_subscription_plans_billing_period'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('institution_id', sa.Uuid(), nullable=True),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('next_renewal_date', sa.DateTime(), nullable=True),
        sa.Column('cancellation_date', sa.DateTime(), nullable=True),
        sa.Column('grace_period_end', sa.DateTime(), nullable=True),
        sa.Column('trial_duration_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.CheckConstraint(
            "status IN ('trial', 'active', 'overdue', 'grace_period', 'expired', 'cancelled')",
            name='ck_subscriptions_status'
        ),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND institution_id IS NULL) OR (user_id IS NULL AND institution_id IS NOT NULL)",
            name='ck_subscriptions_exactly_one_owner'
        ),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create partial unique indexes for subscriptions
    # These prevent multiple active subscriptions per user/institution
    op.create_index(
        'idx_subscriptions_active_user',
        'subscriptions',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('trial', 'active', 'overdue', 'grace_period')"),
        sqlite_where="status IN ('trial', 'active', 'overdue', 'grace_period')"
    )
    
    op.create_index(
        'idx_subscriptions_active_institution',
        'subscriptions',
        ['institution_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('trial', 'active', 'overdue', 'grace_period')"),
        sqlite_where="status IN ('trial', 'active', 'overdue', 'grace_period')"
    )
    
    # Create billing_records table
    op.create_table(
        'billing_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('billing_date', sa.DateTime(), nullable=False),
        sa.Column('payment_status', sa.String(length=20), nullable=False),
        sa.Column('payment_method_ref', sa.String(length=100), nullable=True),
        sa.Column('transaction_ref', sa.String(length=100), nullable=True),
        sa.CheckConstraint(
            "payment_status IN ('paid', 'pending', 'failed')",
            name='ck_billing_records_payment_status'
        ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('institution_id', sa.Uuid(), nullable=True),
        sa.Column('submission_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sa.String(length=32), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('billing_period_start', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create subscription_events table
    op.create_table(
        'subscription_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('subscription_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(length=20), nullable=False),
        sa.Column('previous_status', sa.String(length=20), nullable=False),
        sa.Column('new_status', sa.String(length=20), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.CheckConstraint(
            "event_type IN ('activated', 'renewed', 'overdue', 'grace_period', 'expired', 'cancelled', 'reactivated', 'upgraded')",
            name='ck_subscription_events_event_type'
        ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('institution_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('consumed_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'consumed', 'expired')",
            name='ck_invitations_status'
        ),
        sa.ForeignKeyConstraint(['consumed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_invitations_code')
    )
    
    # =========================================================================
    # DDL: Modify users table
    # =========================================================================
    
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add new columns
        batch_op.add_column(sa.Column('student_subtype', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('institution_id', sa.Uuid(), nullable=True))
        
        # Drop old role CHECK constraint
        batch_op.drop_constraint('ck_users_role', type_='check')
        
        # Alter role column to accommodate longer role names (institution_admin = 18 chars)
        batch_op.alter_column('role',
                              existing_type=sa.String(length=16),
                              type_=sa.String(length=20),
                              existing_nullable=False)
        
        # Add new role CHECK constraint with 3 roles
        batch_op.create_check_constraint(
            'ck_users_role',
            "role IN ('platform_admin', 'institution_admin', 'student')"
        )
        
        # Add student_subtype CHECK constraint
        batch_op.create_check_constraint(
            'ck_users_student_subtype',
            "student_subtype IN ('direct_subscriber', 'institution_linked', 'dual') OR student_subtype IS NULL"
        )
        
        # Add foreign key to institutions
        batch_op.create_foreign_key(
            'fk_users_institution_id_institutions',
            'institutions',
            ['institution_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    """Downgrade schema - remove subscription platform tables and revert users table."""
    
    # =========================================================================
    # Revert users table modifications
    # =========================================================================
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Drop foreign key to institutions
        batch_op.drop_constraint('fk_users_institution_id_institutions', type_='foreignkey')
        
        # Drop new CHECK constraints
        batch_op.drop_constraint('ck_users_student_subtype', type_='check')
        batch_op.drop_constraint('ck_users_role', type_='check')
        
        # Restore original role CHECK constraint
        batch_op.create_check_constraint(
            'ck_users_role',
            "role IN ('student', 'admin')"
        )
        
        # Revert role column width
        batch_op.alter_column('role',
                              existing_type=sa.String(length=20),
                              type_=sa.String(length=16),
                              existing_nullable=False)
        
        # Drop new columns
        batch_op.drop_column('institution_id')
        batch_op.drop_column('student_subtype')
    
    # =========================================================================
    # Drop new tables (in reverse order of creation due to foreign keys)
    # =========================================================================
    
    op.drop_table('invitations')
    op.drop_table('subscription_events')
    op.drop_table('usage_records')
    op.drop_table('billing_records')
    
    # Drop indexes before dropping subscriptions table
    op.drop_index('idx_subscriptions_active_institution', table_name='subscriptions')
    op.drop_index('idx_subscriptions_active_user', table_name='subscriptions')
    
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('institutions')
