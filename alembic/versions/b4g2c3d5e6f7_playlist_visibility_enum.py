"""Replace is_public bool with visibility string on playlists

Revision ID: b4g2c3d5e6f7
Revises: a3f1b2c4d5e6
Create Date: 2026-04-22 11:00:00.000000

Migrates is_public (boolean) → visibility (varchar 20).
Values: 'private' (default), 'public', 'unlisted' (accessible by link, not listed).
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4g2c3d5e6f7'
down_revision = 'a3f1b2c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('playlists', sa.Column('visibility', sa.String(20), nullable=False, server_default='private'))
    # Carry over any rows that were already marked public
    op.execute("UPDATE playlists SET visibility = 'public' WHERE is_public = true")
    op.drop_column('playlists', 'is_public')


def downgrade():
    op.add_column('playlists', sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.execute("UPDATE playlists SET is_public = true WHERE visibility = 'public'")
    op.drop_column('playlists', 'visibility')
