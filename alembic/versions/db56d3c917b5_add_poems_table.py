"""add_poems_table

Revision ID: db56d3c917b5
Revises: 26cc6bab6900
Create Date: 2026-05-29 10:45:37.640710

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'db56d3c917b5'
down_revision = '26cc6bab6900'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('poems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poem_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('poet_name', sa.String(length=255), nullable=False),
        sa.Column('poet_slug', sa.String(length=255), nullable=True),
        sa.Column('body_text', sa.String(length=20000), nullable=False),
        sa.Column('handwriting_image_url', sa.String(length=1024), nullable=True),
        sa.Column('note', sa.String(length=2000), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('is_published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poems_is_published'), 'poems', ['is_published'], unique=False)
    op.create_index(op.f('ix_poems_poem_id'), 'poems', ['poem_id'], unique=True)
    op.create_index(op.f('ix_poems_poet_slug'), 'poems', ['poet_slug'], unique=False)
    op.create_index(op.f('ix_poems_position'), 'poems', ['position'], unique=False)
    op.create_index(op.f('ix_poems_published_at'), 'poems', ['published_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_poems_published_at'), table_name='poems')
    op.drop_index(op.f('ix_poems_position'), table_name='poems')
    op.drop_index(op.f('ix_poems_poet_slug'), table_name='poems')
    op.drop_index(op.f('ix_poems_poem_id'), table_name='poems')
    op.drop_index(op.f('ix_poems_is_published'), table_name='poems')
    op.drop_table('poems')
