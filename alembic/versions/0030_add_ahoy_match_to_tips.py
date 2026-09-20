"""Add ahoy_match column to tips

Revision ID: 0030_ahoy_match_tips
Revises: 3734478849be
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa


revision = "0030_ahoy_match_tips"
down_revision = "3734478849be"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tips") as batch_op:
        batch_op.add_column(
            sa.Column(
                "ahoy_match",
                sa.Numeric(10, 2),
                nullable=True,
                server_default="0.00",
            )
        )


def downgrade():
    with op.batch_alter_table("tips") as batch_op:
        batch_op.drop_column("ahoy_match")
