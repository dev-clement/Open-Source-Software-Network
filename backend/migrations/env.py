from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import SQLModel metadata so Alembic can detect the current schema.
# Importing the models module as a side-effect registers all table definitions
# on the shared SQLModel.metadata object.
from sqlmodel import SQLModel
import app.db.models  # noqa: F401 – side-effect import to register table metadata

# Import the application settings to obtain the synchronous database URL.
from app.core.settings import get_psql_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel.metadata contains all table definitions registered via SQLModel
# models.  Alembic uses this for autogenerate support.
target_metadata = SQLModel.metadata

# Override the sqlalchemy.url from the application settings so that database
# credentials are never stored inside alembic.ini.
settings = get_psql_settings()
config.set_main_option("sqlalchemy.url", settings.sync_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
