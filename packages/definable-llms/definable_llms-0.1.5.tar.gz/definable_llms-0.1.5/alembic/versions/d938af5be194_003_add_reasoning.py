"""003_add_reasoning

Revision ID: d938af5be194
Revises: 2e9a0d0350ee
Create Date: 2025-10-07 14:21:57.880392

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d938af5be194"
down_revision: Union[str, Sequence[str], None] = "2e9a0d0350ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Add supports_reasoning column to model_registry table."""
  op.add_column(
    "model_registry",
    sa.Column("supports_reasoning", sa.Boolean(), nullable=False, server_default="0"),
  )


def downgrade() -> None:
  """Remove supports_reasoning column from model_registry table."""
  op.drop_column("model_registry", "supports_reasoning")
