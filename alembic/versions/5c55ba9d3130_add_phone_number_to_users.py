"""add_phone_number_to_users

Revision ID: 5c55ba9d3130
Revises: 082d465b0d6d
Create Date: 2026-07-02 10:20:24.265155

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5c55ba9d3130'
down_revision = '082d465b0d6d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column('users', 'phone_number')
