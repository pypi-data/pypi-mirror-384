from __future__ import annotations
import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
# from sqlalchemy.engine.url import make_url

from alembic import context

# Import BIOMERO.importer Base (only migrate BIOMERO.importer tables)
# adjust if Base lives elsewhere
from biomero_importer.utils.ingest_tracker import Base as ADIBase

# Alembic Config provides access to values within the .ini in use.
config = context.config


def _resolve_db_url() -> str | None:
    """Resolve DB URL from env (no SQLite fallback)."""
    return (
        os.getenv("INGEST_TRACKING_DB_URL")
        or os.getenv("SQLALCHEMY_URL")
    )


# Respect URL passed by programmatic Config; otherwise resolve from env.
if not config.get_main_option("sqlalchemy.url"):
    db_url = _resolve_db_url()
    if not db_url:
        raise RuntimeError(
            "Alembic: no sqlalchemy.url. Set INGEST_TRACKING_DB_URL or "
            "SQLALCHEMY_URL, or pass sqlalchemy.url via Config."
        )
    config.set_main_option("sqlalchemy.url", db_url)

# Use a per-project version table in the same schema
config.set_main_option("version_table", "alembic_version_omeroadi")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger(__name__)

target_metadata = ADIBase.metadata

# Only include our own tables in autogenerate


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in target_metadata.tables
    if type_ == "index":
        tbl = object.table.name if hasattr(object, "table") else None
        return tbl in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        version_table=config.get_main_option("version_table"),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        backend = getattr(connection.dialect, "name", "unknown")
        logger.info(f"Alembic backend: {backend}")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            version_table=config.get_main_option("version_table"),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
