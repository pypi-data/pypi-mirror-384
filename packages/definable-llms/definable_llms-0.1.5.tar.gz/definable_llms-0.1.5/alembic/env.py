from logging.config import fileConfig
import sys
import asyncio
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Add your project to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import your models and config
from definable.llms.database.schema import Base
from definable.llms.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
  fileConfig(config.config_file_name)

# Set target metadata to your database models
target_metadata = Base.metadata


def get_database_url():
  """Get async database URL for migrations."""
  return settings.db_url


def run_migrations_offline() -> None:
  """Run migrations in 'offline' mode.

  This configures the context with just a URL
  and not an Engine, though an Engine is acceptable
  here as well.  By skipping the Engine creation
  we don't even need a DBAPI to be available.

  Calls to context.execute() here emit the given string to the
  script output.

  """
  url = get_database_url()
  context.configure(
    url=url,
    target_metadata=target_metadata,
    literal_binds=True,
    dialect_opts={"paramstyle": "named"},
  )

  with context.begin_transaction():
    context.run_migrations()


def run_migrations_online() -> None:
  """Run migrations in 'online' mode with async engine.

  In this scenario we need to create an async Engine
  and associate a connection with the context.

  """
  connectable = create_async_engine(
    get_database_url(),
    poolclass=pool.NullPool,
  )

  async def run_async_migrations():
    async with connectable.connect() as connection:
      await connection.run_sync(do_run_migrations)
    await connectable.dispose()

  def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
      context.run_migrations()

  asyncio.run(run_async_migrations())


if context.is_offline_mode():
  run_migrations_offline()
else:
  run_migrations_online()
