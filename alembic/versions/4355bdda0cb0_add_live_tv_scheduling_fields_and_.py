"""add ahoy tv scheduling fields and schedule table

Revision ID: 4355bdda0cb0
Revises: 0028_seed_pnf_videos
Create Date: 2026-03-22 08:06:49.147623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4355bdda0cb0'
down_revision = '0028_seed_pnf_videos'
branch_labels = None
depends_on = None


def upgrade():
    # Add fields to content_shows
    op.add_column('content_shows', sa.Column('is_new', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('content_shows', sa.Column('featured_until', sa.Date(), nullable=True))

    # Create live_tv_schedule table
    op.create_table('live_tv_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False, index=True),
        sa.Column('slot_id', sa.Integer(), nullable=False, index=True),  # 0-95
        sa.Column('channel_id', sa.String(50), nullable=False, index=True),  # 'misc', 'films', 'music-videos', 'live-shows'
        sa.Column('show_id', sa.Integer(), nullable=True),  # nullable for empty slots
        sa.Column('filler_queue', sa.JSON(), nullable=False, server_default='[]'),  # list of show IDs
        sa.Column('is_prime_time', sa.Boolean(), nullable=False, default=False),
        sa.Column('weight_used', sa.String(50), nullable=False, default='random'),  # 'new' or 'random'
        sa.ForeignKeyConstraint(['show_id'], ['content_shows.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schedule_date', 'slot_id', 'channel_id', name='uq_schedule_date_slot_channel')
    )
    op.create_index('ix_live_tv_schedule_date_channel', 'live_tv_schedule', ['schedule_date', 'channel_id'], unique=False)


def downgrade():
    op.drop_table('live_tv_schedule')
    op.drop_column('content_shows', 'featured_until')
    op.drop_column('content_shows', 'is_new')
