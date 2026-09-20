"""merge heads 0029 and a1b2c3d4e5f6

Revision ID: 3734478849be
Revises: 0029_google_oauth, a1b2c3d4e5f6
Create Date: 2026-03-27 17:10:24.845812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3734478849be'
down_revision = ('0029_google_oauth', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
