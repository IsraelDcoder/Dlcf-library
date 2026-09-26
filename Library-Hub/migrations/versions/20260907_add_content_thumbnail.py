"""add content thumbnail

Revision ID: 20260907_add_content_thumbnail
Revises:
Create Date: 2026-09-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260907_add_content_thumbnail"
down_revision = "20251228_add_live_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content", sa.Column("thumbnail", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("content", "thumbnail")
