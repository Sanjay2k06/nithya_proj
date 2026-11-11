"""Persist human-readable source names with incidents.

Revision ID: 3c5a1f8d2b74
Revises: 2a7c8e4d91bf
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa


revision = "3c5a1f8d2b74"
down_revision = "2a7c8e4d91bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("source_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "source_name")
