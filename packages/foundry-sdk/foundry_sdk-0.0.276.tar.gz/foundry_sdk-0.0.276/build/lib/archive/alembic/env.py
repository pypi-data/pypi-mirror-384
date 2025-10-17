import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

from alembic import context

# Add root to sys.path so we can import foundry_sdk
sys.path.append(str(Path(__file__).resolve().parents[1]))

from foundry_sdk.db_mgmt.tables import Base

# Load environment variables from .env file
load_dotenv()

# Load SQLAlchemy Base


# Alembic Config object
config = context.config

# Set up loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set metadata for 'autogenerate' support
target_metadata = Base.metadata

# Load DB connection string from .env
SQLALCHEMY_URL = os.getenv("DB_CONNECTION_STRING")
if SQLALCHEMY_URL is None:
    raise RuntimeError("Environment variable DB_CONNECTION_STRING is not set.")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL.
    """
    context.configure(
        url=SQLALCHEMY_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    This creates an Engine and associates a connection with the context.
    """
    connectable = create_engine(SQLALCHEMY_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
    run_migrations_online()
