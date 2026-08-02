"""Add institution scoping to questions and exams

Revision ID: 0006_add_institution_scoping
Revises: 0005_migrate_user_data
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006_add_institution_scoping'
down_revision = '0005_migrate_user_data'
branch_labels = None
depends_on = None


def upgrade():
    """Add institution_id to questions and exams tables for institution-scoped content."""
    
    # Add institution_id to questions table
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            'fk_questions_institution_id',
            'institutions',
            ['institution_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_index('idx_questions_institution_id', ['institution_id'])
    
    # Add institution_id to exams table
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.add_column(sa.Column('institution_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            'fk_exams_institution_id',
            'institutions',
            ['institution_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_index('idx_exams_institution_id', ['institution_id'])


def downgrade():
    """Remove institution scoping from questions and exams."""
    
    # Remove from exams
    with op.batch_alter_table('exams', schema=None) as batch_op:
        batch_op.drop_index('idx_exams_institution_id')
        batch_op.drop_constraint('fk_exams_institution_id', type_='foreignkey')
        batch_op.drop_column('institution_id')
    
    # Remove from questions
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_index('idx_questions_institution_id')
        batch_op.drop_constraint('fk_questions_institution_id', type_='foreignkey')
        batch_op.drop_column('institution_id')
