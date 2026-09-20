"""add_is_new_and_skip_feature_to_whats_new

Revision ID: 082d465b0d6d
Revises: b898230e4559
Create Date: 2026-06-05 10:21:57.364285

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '082d465b0d6d'
down_revision = 'b898230e4559'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_whats_new', sa.Column('is_new', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('content_whats_new', sa.Column('skip_feature', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_content_whats_new_is_new'), 'content_whats_new', ['is_new'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_content_whats_new_is_new'), table_name='content_whats_new')
    op.drop_column('content_whats_new', 'skip_feature')
    op.drop_column('content_whats_new', 'is_new')
