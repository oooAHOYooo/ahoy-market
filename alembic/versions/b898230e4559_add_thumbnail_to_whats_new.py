"""add_thumbnail_to_whats_new

Revision ID: b898230e4559
Revises: db56d3c917b5
Create Date: 2026-06-05 09:44:58.767124

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b898230e4559'
down_revision = 'db56d3c917b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_whats_new', sa.Column('thumbnail', sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column('content_whats_new', 'thumbnail')
