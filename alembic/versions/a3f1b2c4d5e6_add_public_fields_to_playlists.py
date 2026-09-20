"""Add is_public and description to playlists

Revision ID: a3f1b2c4d5e6
Revises: f0f9b3832b09
Create Date: 2026-04-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f1b2c4d5e6'
down_revision = 'f0f9b3832b09'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('playlists', sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('playlists', sa.Column('description', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('playlists', 'description')
    op.drop_column('playlists', 'is_public')
