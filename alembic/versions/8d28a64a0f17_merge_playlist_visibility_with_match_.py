"""merge playlist visibility with match tips head

Revision ID: 8d28a64a0f17
Revises: 0030_ahoy_match_tips, b4g2c3d5e6f7
Create Date: 2026-04-22 12:34:14.169699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d28a64a0f17'
down_revision = ('0030_ahoy_match_tips', 'b4g2c3d5e6f7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
