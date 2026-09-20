"""add video_url to podcast episodes

Revision ID: 26cc6bab6900
Revises: c5d6e7f8a9b0
Create Date: 2026-05-22 12:41:38.144099

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '26cc6bab6900'
down_revision = 'c5d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_podcast_episodes', sa.Column('video_url', sa.String(length=1024), server_default='', nullable=False))


def downgrade():
    op.drop_column('content_podcast_episodes', 'video_url')
