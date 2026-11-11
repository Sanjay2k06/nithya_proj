"""Persist source IDs for detections and incident deduplication.

Revision ID: 2a7c8e4d91bf
Revises: 9f5c2a8b7d31
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa


revision = "2a7c8e4d91bf"
down_revision = "9f5c2a8b7d31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("detections", sa.Column("source_id", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_detections_source_id"), "detections", ["source_id"], unique=False)
    op.add_column("alerts", sa.Column("source_id", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_alerts_source_id"), "alerts", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_source_id"), table_name="alerts")
    op.drop_column("alerts", "source_id")
    op.drop_index(op.f("ix_detections_source_id"), table_name="detections")
    op.drop_column("detections", "source_id")
