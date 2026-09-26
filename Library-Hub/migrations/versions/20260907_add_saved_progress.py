"""add saved resources and learning progress

Revision ID: 20260907_add_saved_progress
Revises: 20260907_add_content_thumbnail
Create Date: 2026-09-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260907_add_saved_progress"
down_revision = "20260907_add_content_thumbnail"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_resource",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("content.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("user_id", "content_id", name="uq_saved_resource_user_content"),
    )
    op.create_table(
        "learning_progress",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("content.id"), nullable=False),
        sa.Column("progress", sa.Float, nullable=False, server_default="0"),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("user_id", "content_id", name="uq_learning_progress_user_content"),
    )


def downgrade():
    op.drop_table("learning_progress")
    op.drop_table("saved_resource")