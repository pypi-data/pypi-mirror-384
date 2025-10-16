"""Database infrastructure for analytics."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .schema import Base, SessionAnalytics, RequestEvent, ModelRegistry
from .models import SessionAnalyticsModel, RequestEventModel, ModelRegistryModel
from .model_loader import DatabaseModelLoader, db_model_loader

# Global engine and session factory
engine = None
async_session_factory = None


async def init_database(database_url: str):
  """Initialize database connection."""
  global engine, async_session_factory

  engine = create_async_engine(
    database_url,
    echo=False,  # Set True for SQL debugging
    pool_size=10,
    max_overflow=20,
  )

  async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_db_session() -> AsyncSession:
  """Get database session."""
  if not async_session_factory:
    raise RuntimeError("Database not initialized. Call init_database() first.")

  return async_session_factory()


__all__ = [
  "Base",
  "SessionAnalytics",
  "RequestEvent",
  "ModelRegistry",
  "SessionAnalyticsModel",
  "RequestEventModel",
  "ModelRegistryModel",
  "init_database",
  "get_db_session",
  "DatabaseModelLoader",
  "db_model_loader",
]
