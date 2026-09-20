"""Add audit logs table for admin action tracking

Revision ID: 0027_audit_logs
Revises: ba380a3a23dd
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa

revision = '0027_audit_logs'
down_revision = 'ba380a3a23dd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('target_type', sa.String(length=50), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_admin_id'), 'audit_logs', ['admin_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_audit_logs_admin_created_at', 'audit_logs', ['admin_id', 'created_at'], unique=False)


def downgrade():
    op.drop_table('audit_logs')
