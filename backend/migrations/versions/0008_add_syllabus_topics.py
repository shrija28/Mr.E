"""Add KCET syllabus_topics table and syllabus_topic_id on questions

Revision ID: 0008_add_syllabus_topics
Revises: 0007_add_institution_id_to_indexed_files
Create Date: 2026-06-10 10:00:00.000000

Source: KEA / Karnataka Department of Pre-University Education (DPUE)
NCERT Class 11 & 12 syllabus as prescribed for KCET 2026.
Cross-referenced: Deeksha Learning (deekshalearning.com), Aakash (aakash.ac.in)
"""
from alembic import op
import sqlalchemy as sa

revision = '0008_add_syllabus_topics'
down_revision = '0007_add_institution_id_to_indexed_files'
branch_labels = None
depends_on = None


def upgrade():
    # ── syllabus_topics table ────────────────────────────────────────────────
    # Use checkfirst=True to handle cases where the table was already created
    # by SQLAlchemy auto-create on a previous server start.
    op.create_table(
        'syllabus_topics',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('subject', sa.String(32), nullable=False),
        sa.Column('puc_year', sa.String(10), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('chapter_name', sa.String(200), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id', name='pk_syllabus_topics'),
        sa.CheckConstraint(
            "subject IN ('Physics','Chemistry','Mathematics','Biology')",
            name='ck_syllabus_topics_subject',
        ),
        sa.CheckConstraint(
            "puc_year IN ('1st PUC','2nd PUC')",
            name='ck_syllabus_topics_puc_year',
        ),
        sa.UniqueConstraint('subject', 'puc_year', 'chapter_number',
                            name='uq_syllabus_topic_chapter'),
        if_not_exists=True,
    )
    op.create_index('idx_syllabus_topics_subject_puc', 'syllabus_topics',
                    ['subject', 'puc_year'], if_not_exists=True)

    # ── Add syllabus_topic_id FK to questions ────────────────────────────────
    # Check if column already exists before adding
    from sqlalchemy import inspect as sa_inspect
    from alembic import context
    bind = context.get_bind()
    insp = sa_inspect(bind)
    existing_cols = [c['name'] for c in insp.get_columns('questions')]

    if 'syllabus_topic_id' not in existing_cols:
        with op.batch_alter_table('questions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('syllabus_topic_id', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('topic_confidence', sa.String(20), nullable=True))
            batch_op.create_foreign_key(
                'fk_questions_syllabus_topic_id',
                'syllabus_topics',
                ['syllabus_topic_id'],
                ['id'],
                ondelete='SET NULL',
            )
            batch_op.create_index('idx_questions_syllabus_topic_id', ['syllabus_topic_id'])


def downgrade():
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_index('idx_questions_syllabus_topic_id')
        batch_op.drop_constraint('fk_questions_syllabus_topic_id', type_='foreignkey')
        batch_op.drop_column('topic_confidence')
        batch_op.drop_column('syllabus_topic_id')

    op.drop_index('idx_syllabus_topics_subject_puc', 'syllabus_topics')
    op.drop_table('syllabus_topics')
