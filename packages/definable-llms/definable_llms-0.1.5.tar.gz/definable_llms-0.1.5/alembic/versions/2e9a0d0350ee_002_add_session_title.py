"""002_add_session_title

Revision ID: 2e9a0d0350ee
Revises: 2df32d79b873
Create Date: 2025-10-06 18:51:48.683122

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2e9a0d0350ee"
down_revision: Union[str, Sequence[str], None] = "2df32d79b873"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  """Upgrade schema."""
  # Add session title to session analytics and request events
  op.add_column(
    "session_analytics",
    sa.Column("session_title", sa.String(length=200), nullable=False),
  )
  op.add_column(
    "request_events",
    sa.Column("session_title", sa.String(length=200), nullable=False),
  )


def downgrade() -> None:
  """Downgrade schema."""
  # Drop session title from session analytics and request events
  op.drop_column("session_analytics", "session_title")
  op.drop_column("request_events", "session_title")
