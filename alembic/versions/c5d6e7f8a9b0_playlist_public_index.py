"""Add partial index on playlists for public discovery feed

Revision ID: c5d6e7f8a9b0
Revises: 8d28a64a0f17
Create Date: 2026-04-22 13:00:00.000000

Adds a partial index on updated_at WHERE visibility = 'public'.
Used by GET /api/playlists/public (ordered by updated_at DESC).
Postgres-only — SQLite will apply as a full index (no WHERE support).
"""
from alembic import op
import sqlalchemy as sa

revision = 'c5d6e7f8a9b0'
down_revision = '8d28a64a0f17'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_playlists_public_updated_at',
        'playlists',
        ['updated_at'],
        postgresql_where=sa.text("visibility = 'public'"),
    )


def downgrade():
    op.drop_index('ix_playlists_public_updated_at', table_name='playlists')
