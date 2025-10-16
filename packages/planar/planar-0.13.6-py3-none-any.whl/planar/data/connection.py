import asyncio
from dataclasses import dataclass
from typing import cast
from urllib.parse import urlparse

import ibis
from ibis.backends.duckdb import Backend as DuckDBBackend

from planar.config import PlanarConfig
from planar.data.config import (
    PostgresCatalogConfig,
    SQLiteCatalogConfig,
)
from planar.data.exceptions import DataError
from planar.files.storage.config import AzureBlobConfig, LocalDirectoryConfig, S3Config
from planar.logging import get_logger
from planar.session import get_config

logger = get_logger(__name__)


@dataclass
class _ConnectionPool:
    connections: list[DuckDBBackend]
    cursor: int = 0


# In production a Planar app typically runs with a single data config, so we only
# ever have one signature, but we still rotate through a handful of cached
# backends to reduce the risk of concurrent calls sharing the same DuckDB
# connection. During testing we create many ephemeral configs (temp dirs, sqlite
# files, etc.), so the cache also avoids paying the attachment cost on every
# request. We keep up to `_MAX_CONNECTIONS_PER_SIGNATURE` backends per signature
# and hand them out in round-robin order; concurrency safety ultimately depends on
# DuckDB tolerating overlapping use of an individual backend.
_connection_cache: dict[int, _ConnectionPool] = {}
_cache_lock: asyncio.Lock | None = None

# Maximum number of cached connections per configuration signature.
_MAX_CONNECTIONS_PER_SIGNATURE = 10


def _config_signature(config: PlanarConfig) -> int:
    """Create a stable signature for caching connections."""

    assert config.data is not None, "data configuration must be set"
    return hash(config.data)


async def _close_backend(connection: DuckDBBackend) -> None:
    close_fn = getattr(connection, "close", None)
    try:
        if callable(close_fn):
            await asyncio.to_thread(close_fn)
    except Exception as exc:
        logger.warning("failed to close DuckDB connection", error=str(exc))


def _make_aws_s3_secret_query(config: S3Config) -> str:
    """
    https://duckdb.org/docs/stable/core_extensions/httpfs/s3api
    """
    columns = ["TYPE s3"]

    if config.region:
        columns.append(
            f"REGION '{config.region}'",
        )

    if config.endpoint_url:
        parsed_url = urlparse(config.endpoint_url)
        endpoint_host = parsed_url.hostname
        endpoint_port = f":{parsed_url.port}" if parsed_url.port else ""
        endpoint = f"{endpoint_host}{endpoint_port}"

        columns.append(f"ENDPOINT '{endpoint}'")

    if config.access_key and config.secret_key:
        columns.extend(
            [
                "PROVIDER config",
                f"KEY_ID '{config.access_key}'",
                f"SECRET '{config.secret_key}'",
            ]
        )
    else:
        columns.append("PROVIDER credential_chain")

    return f"""
        CREATE OR REPLACE SECRET secret (
        {", ".join(columns)}
        );
    """


async def setup_azure_filesystem(config: AzureBlobConfig):
    from adlfs.spec import AzureBlobFileSystem
    from azure.identity.aio import DefaultAzureCredential

    if config.use_azure_ad:
        account_name = _get_azure_account_name(config)
        async with DefaultAzureCredential() as credential:
            return AzureBlobFileSystem(
                account_name=account_name,
                # the types are wrong for `credential`
                credential=cast(str, credential),
            )

    elif config.connection_string:
        return AzureBlobFileSystem(connection_string=config.connection_string)

    elif config.account_key:
        account_name = _get_azure_account_name(config)
        account_host = None
        if config.account_url:
            parsed_url = urlparse(config.account_url)
            if parsed_url.hostname:
                account_host = f"{parsed_url.scheme}://{parsed_url.hostname}"
                if parsed_url.port:
                    account_host += f":{parsed_url.port}"

        return AzureBlobFileSystem(
            account_name=account_name,
            account_key=config.account_key,
            account_host=account_host or "",
        )

    else:
        raise ValueError("No valid Azure authentication method configured")


def _get_azure_account_name(config: AzureBlobConfig) -> str:
    if config.account_url:
        # Parse account name from URL like https://myaccount.blob.core.windows.net
        parsed_url = urlparse(config.account_url)
        if parsed_url.hostname:
            return parsed_url.hostname.split(".")[0]

    elif config.connection_string:
        # Extract account name from connection string
        # Format: DefaultEndpointsProtocol=https;AccountName=myaccount;...
        for part in config.connection_string.split(";"):
            if part.startswith("AccountName="):
                return part.split("=", 1)[1]

    raise ValueError("account_name cannot be None")


def _make_azure_blob_secret_query(account_name: str) -> str:
    """
    Create DuckDB secret query for Azure Blob Storage using credential_chain.
    https://duckdb.org/docs/stable/core_extensions/azure
    """
    return f"""
        CREATE OR REPLACE SECRET azure_secret (
            TYPE azure,
            PROVIDER credential_chain,
            ACCOUNT_NAME '{account_name}'
        );
    """


async def _create_connection(config: PlanarConfig) -> DuckDBBackend:
    """Create Ibis DuckDB connection with Ducklake."""
    data_config = config.data
    if not data_config:
        raise DataError("Data configuration not found")

    # Connect to DuckDB with Ducklake extension
    con = await asyncio.to_thread(ibis.duckdb.connect, extensions=["ducklake"])

    # Build Ducklake connection string based on catalog type
    catalog_config = data_config.catalog

    match catalog_config:
        case PostgresCatalogConfig():
            # Use connection components to build postgres connection string
            metadata_path = f"postgres:dbname={catalog_config.db}"
            if catalog_config.host:
                metadata_path += f" host={catalog_config.host}"
            if catalog_config.port:
                metadata_path += f" port={catalog_config.port}"
            if catalog_config.user:
                metadata_path += f" user={catalog_config.user}"
            if catalog_config.password:
                metadata_path += f" password={catalog_config.password}"
        case SQLiteCatalogConfig():
            metadata_path = f"sqlite:{catalog_config.path}"
        case _:
            raise ValueError(f"Unsupported catalog type: {catalog_config.type}")

    try:
        await asyncio.to_thread(con.raw_sql, "INSTALL ducklake")
        match catalog_config.type:
            case "sqlite":
                await asyncio.to_thread(con.raw_sql, "INSTALL sqlite;")
            case "postgres":
                await asyncio.to_thread(con.raw_sql, "INSTALL postgres;")
        logger.debug("installed Ducklake extensions", catalog_type=catalog_config.type)
    except Exception as e:
        raise DataError(f"Failed to install Ducklake extensions: {e}") from e

    # Build ATTACH statement
    attach_sql = f"ATTACH 'ducklake:{metadata_path}' AS planar_ducklake"

    # Add data path from storage config
    storage = data_config.storage
    if isinstance(storage, LocalDirectoryConfig):
        data_path = storage.directory
    elif isinstance(storage, S3Config):
        await asyncio.to_thread(con.raw_sql, "INSTALL httpfs;")
        await asyncio.to_thread(con.raw_sql, "LOAD httpfs;")

        await asyncio.to_thread(
            con.raw_sql,
            _make_aws_s3_secret_query(storage),
        )

        data_path = f"s3://{storage.bucket_name}/"
    elif isinstance(storage, AzureBlobConfig):
        await asyncio.to_thread(con.raw_sql, "INSTALL httpfs;")

        account_name = _get_azure_account_name(storage)

        await asyncio.to_thread(
            con.raw_sql,
            _make_azure_blob_secret_query(account_name),
        )

        az_fs = await setup_azure_filesystem(storage)
        await asyncio.to_thread(con.register_filesystem, az_fs)

        data_path = f"abfs://{storage.container_name}/"
    else:
        # Generic fallback
        data_path = getattr(storage, "path", None) or getattr(storage, "directory", ".")

    ducklake_catalog = data_config.catalog_name
    attach_sql += f" (DATA_PATH '{data_path}'"
    if catalog_config.type != "sqlite":
        attach_sql += f", METADATA_SCHEMA '{ducklake_catalog}'"
    attach_sql += ");"

    # Attach to Ducklake
    try:
        await asyncio.to_thread(con.raw_sql, attach_sql)
    except Exception as e:
        raise DataError(f"Failed to attach to Ducklake: {e}") from e

    await asyncio.to_thread(con.raw_sql, "USE planar_ducklake;")
    logger.debug(
        "connection created",
        catalog=ducklake_catalog,
        catalog_type=catalog_config.type,
        attach_sql=attach_sql,
    )

    return con


def _get_cache_lock() -> asyncio.Lock:
    # Create a lock on the first call to this function, or re-create it if the
    # loop has changed (happens on tests).
    global _cache_lock
    loop = asyncio.get_running_loop()
    lock = _cache_lock
    if lock is None or getattr(lock, "_loop", None) is not loop:
        lock = asyncio.Lock()
        _cache_lock = lock
    return lock


async def get_connection() -> DuckDBBackend:
    """Return a cached DuckDB connection using round-robin selection."""

    config = get_config()

    if not config.data:
        raise DataError(
            "Data configuration not found. Please configure 'data' in your planar.yaml"
        )

    signature = _config_signature(config)
    lock = _get_cache_lock()

    async with lock:
        pool = _connection_cache.get(signature)

        if pool is None:
            connection = await _create_connection(config)
            _connection_cache[signature] = _ConnectionPool(connections=[connection])
            return connection

        if len(pool.connections) < _MAX_CONNECTIONS_PER_SIGNATURE:
            connection = await _create_connection(config)
            pool.connections.append(connection)
            return connection

        connection = pool.connections[pool.cursor]
        pool.cursor = (pool.cursor + 1) % len(pool.connections)
        return connection


async def reset_connection_cache() -> None:
    """Reset the cached DuckDB connection, closing it if necessary."""

    lock = _get_cache_lock()

    async with lock:
        pools = list(_connection_cache.values())
        _connection_cache.clear()

    for pool in pools:
        for connection in pool.connections:
            await _close_backend(connection)

    global _cache_lock
    _cache_lock = None
