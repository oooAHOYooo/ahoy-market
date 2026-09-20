"""0026_add_track_play_count

Revision ID: 0026_track_play_count
Revises: 0025_studio_collections
Create Date: 2026-03-13

Add play_count column to content_tracks table.
"""
from alembic import op
import sqlalchemy as sa

revision = '0026_track_play_count'
down_revision = '0025_studio_collections'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_tracks', sa.Column('play_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('content_tracks', 'play_count')
