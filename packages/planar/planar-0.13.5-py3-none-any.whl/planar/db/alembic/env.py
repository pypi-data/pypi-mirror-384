import asyncio
from functools import wraps
from logging.config import fileConfig

import alembic.ddl.base as alembic_base
from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from planar.db import PLANAR_FRAMEWORK_METADATA, PLANAR_SCHEMA

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = PLANAR_FRAMEWORK_METADATA

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    raise NotImplementedError(
        "Offline mode is not supported for Planar system migrations."
    )


def include_name(name, type_, _):
    if type_ == "schema":
        return name == PLANAR_SCHEMA
    else:
        return True


sqlite_schema_translate_map = {PLANAR_SCHEMA: None}


def schema_translate_wrapper(f):
    @wraps(f)
    def format_table_name_with_schema(compiler, name, schema):
        # when on sqlite, we need to translate the schema to None
        is_sqlite = compiler.dialect.name == "sqlite"
        if is_sqlite:
            translated_schema = sqlite_schema_translate_map.get(schema, schema)
        else:
            translated_schema = schema
        return f(compiler, name, translated_schema)

    return format_table_name_with_schema


alembic_base.format_table_name = schema_translate_wrapper(
    alembic_base.format_table_name
)


async def run_migrations_online_async() -> None:
    """Run migrations in 'online' mode using async engine for development."""
    # Import models to ensure they're registered with PLANAR_FRAMEWORK_METADATA
    try:
        from planar.files.models import PlanarFileMetadata  # noqa: F401, PLC0415
        from planar.human.models import HumanTask  # noqa: F401, PLC0415
        from planar.object_config.models import (  # noqa: F401, PLC0415
            ObjectConfiguration,
        )
        from planar.workflows.models import (  # noqa: PLC0415
            LockedResource,  # noqa: F401
            Workflow,  # noqa: F401
            WorkflowEvent,  # noqa: F401
            WorkflowStep,  # noqa: F401
        )
    except ImportError as e:
        raise RuntimeError(
            f"Failed to import system models for migration generation: {e}"
        )

    config_dict = config.get_section(config.config_ini_section, {})
    url = config_dict["sqlalchemy.url"]
    is_sqlite = url.startswith("sqlite://")

    # Create async engine
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        execution_options={
            # SQLite doesn't support schemas, so we need to translate the planar schema
            # name to None in order to ignore it.
            "schema_translate_map": sqlite_schema_translate_map if is_sqlite else {},
        },
    )

    async with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        if is_sqlite:
            connection.dialect.default_schema_name = PLANAR_SCHEMA

        def do_run_migrations(sync_conn):
            context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
                # For SQLite, don't use schema since it's not supported
                version_table_schema=None if is_sqlite else PLANAR_SCHEMA,
                include_schemas=True,
                include_name=include_name,
                # SQLite doesn't support alter table, so we need to use render_as_batch
                # to create the tables in a single transaction. For other databases,
                # the batch op is no-op.
                # https://alembic.sqlalchemy.org/en/latest/batch.html#running-batch-migrations-for-sqlite-and-other-databases
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Check if we're being called programmatically (runtime) or from command line (development)
    connectable = config.attributes.get("connection", None)

    if isinstance(connectable, Connection):
        # Runtime mode: use the connection passed by DatabaseManager
        is_sqlite = connectable.dialect.name == "sqlite"

        context.configure(
            connection=connectable,
            target_metadata=target_metadata,
            # For SQLite, don't use schema since it's not supported
            version_table_schema=None if is_sqlite else PLANAR_SCHEMA,
            include_schemas=True,
            include_name=include_name,
            # SQLite doesn't support alter table, so we need to use render_as_batch
            # to create the tables in a single transaction. For other databases,
            # the batch op is no-op.
            # https://alembic.sqlalchemy.org/en/latest/batch.html#running-batch-migrations-for-sqlite-and-other-databases
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()
    else:
        # Development mode: run migrations asynchronously
        asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
