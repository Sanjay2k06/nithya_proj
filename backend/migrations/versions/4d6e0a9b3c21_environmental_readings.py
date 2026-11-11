"""Store optional, source-associated environmental sensor readings.

Revision ID: 4d6e0a9b3c21
Revises: 3c5a1f8d2b74
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa


revision = "4d6e0a9b3c21"
down_revision = "3c5a1f8d2b74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table_name = "environmental_readings"
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table_name):
        op.create_table(
            table_name,
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("source_id", sa.String(length=128), nullable=False),
            sa.Column("temperature_c", sa.Float(), nullable=True),
            sa.Column("humidity_percent", sa.Float(), nullable=True),
            sa.Column("wind_speed_mps", sa.Float(), nullable=True),
            sa.Column("wind_direction_degrees", sa.Float(), nullable=True),
            sa.Column("smoke_sensor_value", sa.Float(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(op.get_bind())

    required_columns = {
        "id",
        "source_id",
        "temperature_c",
        "humidity_percent",
        "wind_speed_mps",
        "wind_direction_degrees",
        "smoke_sensor_value",
        "recorded_at",
        "created_at",
    }
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if not required_columns.issubset(existing_columns):
        missing = sorted(required_columns - existing_columns)
        raise RuntimeError(f"{table_name} is missing expected columns: {missing}")

    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    for column_name in ("source_id", "recorded_at"):
        index_name = op.f(f"ix_environmental_readings_{column_name}")
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, [column_name], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_environmental_readings_recorded_at"), table_name="environmental_readings")
    op.drop_index(op.f("ix_environmental_readings_source_id"), table_name="environmental_readings")
    op.drop_table("environmental_readings")
