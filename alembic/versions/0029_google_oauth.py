"""0029_google_oauth

Add Google OAuth support: google_id column and make password_hash nullable for Google-only accounts.

Revision ID: 0029_google_oauth
Revises: 0028_seed_pnf_videos
Create Date: 2026-03-26

"""

from alembic import op
import sqlalchemy as sa


revision = '0029_google_oauth'
down_revision = '0028_seed_pnf_videos'
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        cols = [c['name'] for c in insp.get_columns(table)]
        return column in cols
    except Exception:
        return False


def upgrade() -> None:
    # Add google_id column
    if not _has_column('users', 'google_id'):
        op.add_column('users', sa.Column('google_id', sa.String(length=255), nullable=True))

    # Create unique index on google_id (PostgreSQL: partial index where not null)
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    try:
        if dialect_name == 'postgresql':
            op.create_index(
                'ix_users_google_id',
                'users',
                ['google_id'],
                unique=True,
                postgresql_where=sa.text("google_id IS NOT NULL")
            )
        else:
            op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
    except Exception:
        # index may already exist
        pass

    # Make password_hash nullable (allows Google-only accounts with no password)
    try:
        op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=True)
    except Exception:
        # May fail on some DB systems; non-fatal
        pass


def downgrade() -> None:
    # Drop index
    try:
        op.drop_index('ix_users_google_id', table_name='users')
    except Exception:
        pass

    # Drop google_id column if exists
    if _has_column('users', 'google_id'):
        try:
            op.drop_column('users', 'google_id')
        except Exception:
            pass

    # Restore password_hash NOT NULL constraint
    try:
        op.alter_column('users', 'password_hash', existing_type=sa.String(255), nullable=False)
    except Exception:
        # May fail on some DB systems; non-fatal
        pass
