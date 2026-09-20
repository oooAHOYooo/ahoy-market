"""Add the stable AHOY ID subject mapping to users."""
from alembic import op
import sqlalchemy as sa

revision = "0013_add_ahoy_id"
# The repository currently has two migration heads; make this migration the
# convergence point so deploys do not leave an additional branch behind.
down_revision = "74b3084940a4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("ahoy_id", sa.String(length=64), nullable=True))
    op.create_index("ix_users_ahoy_id", "users", ["ahoy_id"], unique=True)


def downgrade():
    op.drop_index("ix_users_ahoy_id", table_name="users")
    op.drop_column("users", "ahoy_id")
