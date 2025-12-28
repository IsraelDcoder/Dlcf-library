"""add live_session table

Revision ID: 20251228_add_live_session
Revises: 
Create Date: 2025-12-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251228_add_live_session'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'live_session',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('host_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('community_id', sa.Integer, sa.ForeignKey('community.id')),
        sa.Column('is_live', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('recording_path', sa.String(length=500), nullable=True),
        sa.Column('recording_size', sa.Integer, nullable=True),
        sa.Column('is_saved', sa.Boolean, nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime, nullable=True)
    )

    # association table for live session tags
    op.create_table(
        'live_session_tags',
        sa.Column('live_session_id', sa.Integer, sa.ForeignKey('live_session.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer, sa.ForeignKey('tag.id'), primary_key=True)
    )


def downgrade():
    op.drop_table('live_session')
