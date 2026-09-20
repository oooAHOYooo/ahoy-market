"""Add is_clip to podcast episodes

Revision ID: a1b2c3d4e5f6
Revises: 62cf584f9527
Branch Labels: None
Depends On: None

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '4355bdda0cb0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_podcast_episodes', sa.Column('is_clip', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade():
    op.drop_column('content_podcast_episodes', 'is_clip')
