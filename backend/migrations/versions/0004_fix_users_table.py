"""fix users table for subscription platform

This migration completes the users table modifications that were missing
from the 0003 migration:
- Adds student_subtype and institution_id columns
- Updates role CHECK constraint to support 3 roles
- Widens role column from VARCHAR(16) to VARCHAR(20)

Revision ID: 0004_fix_users_table
Revises: 0003_subscription_platform_upgrade
Create Date: 2026-05-19 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_fix_users_table'
down_revision: Union[str, Sequence[str], None] = '0003_subscription_platform_upgrade'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - complete users table modifications."""
    
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
    """Downgrade schema - revert users table modifications."""
    
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
