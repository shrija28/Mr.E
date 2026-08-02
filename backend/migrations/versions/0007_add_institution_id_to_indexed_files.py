"""Add institution_id to indexed_files for institution upload scoping

Revision ID: 0007_add_institution_id_to_indexed_files
Revises: 0006_add_institution_scoping
Create Date: 2026-06-09 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0007_add_institution_id_to_indexed_files'
down_revision = '0006_add_institution_scoping'
branch_labels = None
depends_on = None


def upgrade():
    """Add institution_id to indexed_files and relax the unique constraint
    so admin and institution files are scoped separately."""

    with op.batch_alter_table('indexed_files', schema=None) as batch_op:
        # Allow institution_id to be NULL (admin files) or a UUID (institution files)
        batch_op.add_column(sa.Column('institution_id', sa.Uuid(), nullable=True))

        # Drop the old unique constraint (subject, file_hash) — the same PDF
        # can be uploaded by both the admin and multiple institutions.
        batch_op.drop_constraint('uq_subject_file_hash', type_='unique')

        # New constraint: (subject, file_hash, institution_id) — NULL-safe because
        # SQLite/PostgreSQL treat NULLs as distinct in unique indexes.
        batch_op.create_unique_constraint(
            'uq_indexed_files_subject_hash_institution',
            ['subject', 'file_hash', 'institution_id'],
        )

        batch_op.create_index('idx_indexed_files_institution_id', ['institution_id'])


def downgrade():
    with op.batch_alter_table('indexed_files', schema=None) as batch_op:
        batch_op.drop_index('idx_indexed_files_institution_id')
        batch_op.drop_constraint(
            'uq_indexed_files_subject_hash_institution', type_='unique'
        )
        batch_op.create_unique_constraint(
            'uq_subject_file_hash', ['subject', 'file_hash']
        )
        batch_op.drop_column('institution_id')
