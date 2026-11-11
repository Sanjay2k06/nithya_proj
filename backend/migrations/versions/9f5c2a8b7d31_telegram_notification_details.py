"""Add Telegram delivery details and standalone test notifications.

Revision ID: 9f5c2a8b7d31
Revises: 13c861c2e1e4
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa


revision = "9f5c2a8b7d31"
down_revision = "13c861c2e1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notification_logs") as batch_op:
        batch_op.alter_column(
            "alert_id",
            existing_type=sa.String(length=36),
            existing_nullable=False,
            nullable=True,
        )
        batch_op.add_column(sa.Column("recipient", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("evidence_path", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("notification_logs") as batch_op:
        batch_op.drop_column("retry_count")
        batch_op.drop_column("evidence_path")
        batch_op.drop_column("message")
        batch_op.drop_column("recipient")
        batch_op.alter_column(
            "alert_id",
            existing_type=sa.String(length=36),
            existing_nullable=True,
            nullable=False,
        )
