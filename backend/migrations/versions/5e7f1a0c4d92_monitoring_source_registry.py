"""Persist demo source metadata and current service status.

Revision ID: 5e7f1a0c4d92
Revises: 4d6e0a9b3c21
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa


revision = "5e7f1a0c4d92"
down_revision = "4d6e0a9b3c21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table_name = "monitoring_sources"
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        op.create_table(
            table_name,
            sa.Column("id", sa.String(length=128), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("source_type", sa.String(length=64), nullable=False),
            sa.Column("video_filename", sa.String(length=255), nullable=False),
            sa.Column("source_status", sa.String(length=20), nullable=False),
            sa.Column("playback_status", sa.String(length=20), nullable=False),
            sa.Column("processing_status", sa.String(length=20), nullable=False),
            sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_processed_video_seconds", sa.Float(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        return

    required_columns = {
        "id",
        "name",
        "source_type",
        "video_filename",
        "source_status",
        "playback_status",
        "processing_status",
        "last_processed_at",
        "last_processed_video_seconds",
        "updated_at",
    }
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if not required_columns.issubset(existing_columns):
        missing = sorted(required_columns - existing_columns)
        raise RuntimeError(f"{table_name} is missing expected columns: {missing}")


def downgrade() -> None:
    op.drop_table("monitoring_sources")
