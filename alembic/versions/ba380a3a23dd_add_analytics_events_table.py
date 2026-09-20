"""Add analytics events table

Revision ID: ba380a3a23dd
Revises: 0026_track_play_count
Create Date: 2026-03-16 14:13:23.143429

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'ba380a3a23dd'
down_revision = '0026_track_play_count'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('analytics_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_events_created_at'), 'analytics_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_analytics_events_event_type'), 'analytics_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_analytics_events_path'), 'analytics_events', ['path'], unique=False)
    op.create_index(op.f('ix_analytics_events_session_id'), 'analytics_events', ['session_id'], unique=False)
    op.create_index('ix_analytics_events_type_created_at', 'analytics_events', ['event_type', 'created_at'], unique=False)
    op.create_index(op.f('ix_analytics_events_user_id'), 'analytics_events', ['user_id'], unique=False)

def downgrade():
    op.drop_table('analytics_events')
