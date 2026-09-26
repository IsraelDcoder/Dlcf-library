"""add Supabase Auth identity mapping

Revision ID: 20260926_add_supabase_identity
Revises: 20260907_add_saved_progress
Create Date: 2026-09-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20260926_add_supabase_identity"
down_revision = "20260907_add_saved_progress"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content", sa.Column("storage_bucket", sa.String(length=100), nullable=True))
    op.add_column("content", sa.Column("thumbnail_bucket", sa.String(length=100), nullable=True))
    op.add_column("live_session", sa.Column("recording_bucket", sa.String(length=100), nullable=True))
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("supabase_id", sa.String(length=36), nullable=True))
        batch_op.alter_column("password_hash", existing_type=sa.String(length=255), nullable=True)
        batch_op.create_index("ix_user_supabase_id", ["supabase_id"], unique=True)


def downgrade():
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_index("ix_user_supabase_id")
        batch_op.drop_column("supabase_id")
    op.drop_column("live_session", "recording_bucket")
    op.drop_column("content", "thumbnail_bucket")
    op.drop_column("content", "storage_bucket")