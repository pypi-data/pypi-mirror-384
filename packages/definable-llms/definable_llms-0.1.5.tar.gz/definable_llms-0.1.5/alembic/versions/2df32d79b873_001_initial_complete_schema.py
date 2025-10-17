"""001_initial_complete_schema

Revision ID: 2df32d79b873
Revises:
Create Date: 2025-10-01 15:46:26.588795

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2df32d79b873"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  # Create model registry table
  op.create_table(
    "model_registry",
    sa.Column("model_name", sa.String(length=100), nullable=False),
    sa.Column("provider", sa.String(length=50), nullable=False),
    sa.Column("capability", sa.String(length=50), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("display_name", sa.String(length=200), nullable=True),
    sa.Column("input_cost_per_token", sa.DECIMAL(precision=12, scale=10), nullable=False),
    sa.Column("output_cost_per_token", sa.DECIMAL(precision=12, scale=10), nullable=False),
    sa.Column("max_context_length", sa.Integer(), nullable=False),
    sa.Column("max_output_tokens", sa.Integer(), nullable=True),
    sa.Column("supports_streaming", sa.Boolean(), nullable=False),
    sa.Column("supports_functions", sa.Boolean(), nullable=False),
    sa.Column("supports_vision", sa.Boolean(), nullable=False),
    sa.Column("is_active", sa.Boolean(), nullable=False),
    sa.Column("last_updated", sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint("model_name"),
  )
  op.create_index(
    "idx_model_registry_provider_capability",
    "model_registry",
    ["provider", "capability"],
    unique=False,
  )

  # Create session analytics table
  op.create_table(
    "session_analytics",
    sa.Column("session_id", sa.UUID(), nullable=False),
    sa.Column("total_tokens", sa.Integer(), nullable=False),
    sa.Column("total_cost", sa.DECIMAL(precision=10, scale=6), nullable=False),
    sa.Column("request_count", sa.Integer(), nullable=False),
    sa.Column("avg_response_time", sa.DECIMAL(precision=8, scale=3), nullable=False),
    sa.Column("model_usage", sa.JSON(), nullable=False),
    sa.Column("capability_usage", sa.JSON(), nullable=False),
    sa.Column("function_calls", sa.Integer(), nullable=False),
    sa.Column("files_processed", sa.Integer(), nullable=False),
    sa.Column("embeddings_generated", sa.Integer(), nullable=False),
    sa.Column("images_generated", sa.Integer(), nullable=False),
    sa.Column("fastest_response", sa.DECIMAL(precision=8, scale=3), nullable=True),
    sa.Column("slowest_response", sa.DECIMAL(precision=8, scale=3), nullable=True),
    sa.Column("success_rate", sa.DECIMAL(precision=5, scale=4), nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint("session_id"),
  )
  op.create_index(
    "idx_session_analytics_created_at",
    "session_analytics",
    ["created_at"],
    unique=False,
  )

  # Create request events table
  op.create_table(
    "request_events",
    sa.Column("id", sa.UUID(), nullable=False),
    sa.Column("session_id", sa.UUID(), nullable=False),
    sa.Column("request_type", sa.String(length=50), nullable=False),
    sa.Column("model_used", sa.String(length=100), nullable=False),
    sa.Column("provider_used", sa.String(length=50), nullable=False),
    sa.Column("response_time", sa.DECIMAL(precision=8, scale=3), nullable=False),
    sa.Column("tokens_used", sa.Integer(), nullable=False),
    sa.Column("cost", sa.DECIMAL(precision=8, scale=6), nullable=False),
    sa.Column("success", sa.Boolean(), nullable=False),
    sa.Column("error_message", sa.Text(), nullable=True),
    sa.Column("request_size", sa.Integer(), nullable=True),
    sa.Column("response_size", sa.Integer(), nullable=True),
    sa.Column("timestamp", sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(
      ["session_id"],
      ["session_analytics.session_id"],
    ),
    sa.PrimaryKeyConstraint("id"),
  )
  op.create_index("idx_request_events_session_id", "request_events", ["session_id"], unique=False)
  op.create_index("idx_request_events_timestamp", "request_events", ["timestamp"], unique=False)


def downgrade() -> None:
  """Downgrade schema."""
  # Drop request events table
  op.drop_index("idx_request_events_timestamp", table_name="request_events")
  op.drop_index("idx_request_events_session_id", table_name="request_events")
  op.drop_table("request_events")

  # Drop session analytics table
  op.drop_index("idx_session_analytics_created_at", table_name="session_analytics")
  op.drop_table("session_analytics")

  # Drop model registry table
  op.drop_index("idx_model_registry_provider_capability", table_name="model_registry")
  op.drop_table("model_registry")
