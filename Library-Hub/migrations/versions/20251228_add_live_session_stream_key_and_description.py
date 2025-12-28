"""add description, stream_key and thumbnail to live_session

Revision ID: 20251228_add_live_fields
Revises: 20251228_add_live_session
Create Date: 2025-12-28 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251228_add_live_fields'
down_revision = '20251228_add_live_session'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('live_session', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('live_session', sa.Column('stream_key', sa.String(length=255), nullable=True))
    op.add_column('live_session', sa.Column('thumbnail', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('live_session', 'thumbnail')
    op.drop_column('live_session', 'stream_key')
    op.drop_column('live_session', 'description')
