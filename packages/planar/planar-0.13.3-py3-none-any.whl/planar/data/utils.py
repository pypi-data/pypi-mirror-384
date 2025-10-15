import asyncio
from collections import defaultdict
from typing import Sequence, TypedDict

import ibis
import ibis.expr.datatypes as dt
import pyarrow as pa
from ibis.backends.duckdb import Backend as DuckDBBackend
from ibis.common.exceptions import TableNotFound
from sqlglot import exp

from planar.data.connection import get_connection
from planar.data.dataset import PlanarDataset
from planar.data.exceptions import DatasetNotFoundError
from planar.logging import get_logger
from planar.session import get_config

logger = get_logger(__name__)


async def list_datasets(limit: int = 100, offset: int = 0) -> list[PlanarDataset]:
    conn = await get_connection()
    tables = sorted(await asyncio.to_thread(conn.list_tables))[offset : offset + limit]
    return [PlanarDataset(name=table) for table in tables]


async def list_schemas() -> list[str]:
    config = get_config()

    if config.data is None:
        return []

    METADATA_SCHEMAS = [config.data.catalog_name, "main"]

    conn = await get_connection()

    # in ibis, "databases" are schemas in the traditional sense
    # e.g. psql: schema == ibis: database
    # https://ibis-project.org/concepts/backend-table-hierarchy
    schemas = await asyncio.to_thread(conn.list_databases)

    return [schema for schema in schemas if schema in METADATA_SCHEMAS]


async def get_dataset(dataset_name: str, schema_name: str = "main") -> PlanarDataset:
    # TODO: add schema_name as a parameter

    dataset = PlanarDataset(name=dataset_name)

    if not await dataset.exists():
        raise DatasetNotFoundError(f"Dataset {dataset_name} not found")

    return dataset


async def get_dataset_row_count(dataset_name: str) -> int:
    conn = await get_connection()

    try:
        value = await asyncio.to_thread(
            lambda conn, dataset_name: conn.table(dataset_name).count().to_polars(),
            conn,
            dataset_name,
        )

        assert isinstance(value, int), "Scalar must be an integer"

        return value
    except TableNotFound:
        raise  # re-raise the exception and allow the caller to handle it


class DatasetMetadata(TypedDict):
    schema: dict[str, dt.DataType]
    row_count: int


async def _fetch_column_schemas(
    conn: DuckDBBackend,
    dataset_names: Sequence[str],
    schema_name: str,
) -> dict[str, dict[str, dt.DataType]]:
    columns = conn.table("columns", database="information_schema")
    schema_literal = ibis.literal(schema_name)
    dataset_literals = [ibis.literal(name) for name in dataset_names]
    filtered = columns.filter(
        (columns.table_schema == schema_literal)
        & (columns.table_name.isin(dataset_literals))
    )

    selected = filtered.select(
        columns.table_name.name("table_name"),
        columns.column_name.name("column_name"),
        columns.ordinal_position.name("ordinal_position"),
        columns.data_type.name("data_type"),
        columns.is_nullable.name("is_nullable"),
    )

    arrow_table: pa.Table = await asyncio.to_thread(selected.to_pyarrow)
    rows = arrow_table.to_pylist()

    schema_fields: dict[str, list[tuple[int, str, dt.DataType]]] = defaultdict(list)
    type_mapper = conn.compiler.type_mapper

    for row in rows:
        table_name = row["table_name"]
        column_name = row["column_name"]
        ordinal_position = row["ordinal_position"]
        dtype = type_mapper.from_string(
            row["data_type"], nullable=row.get("is_nullable") == "YES"
        )

        schema_fields[table_name].append((ordinal_position, column_name, dtype))

    ordered_fields: dict[str, dict[str, dt.DataType]] = {}
    for table_name, fields in schema_fields.items():
        ordered_fields[table_name] = {
            column_name: dtype
            for _, column_name, dtype in sorted(fields, key=lambda entry: entry[0])
        }

    return ordered_fields


async def _fetch_row_counts(
    conn: DuckDBBackend,
    dataset_names: Sequence[str],
    schema_name: str,
) -> dict[str, int]:
    if not dataset_names:
        return {}

    quoted = conn.compiler.quoted
    count_queries: list[exp.Select] = []

    for dataset_name in dataset_names:
        table_expr = exp.Table(
            this=exp.Identifier(this=dataset_name, quoted=quoted),
            db=(
                exp.Identifier(this=schema_name, quoted=quoted) if schema_name else None
            ),
        )
        select_expr = (
            exp.Select()
            .select(
                exp.Literal.string(dataset_name).as_("dataset_name"),
                exp.Count(this=exp.Star()).as_("row_count"),
            )
            .from_(table_expr)
        )
        count_queries.append(select_expr)

    if not count_queries:
        return {}

    union_query: exp.Expression = count_queries[0]
    for query in count_queries[1:]:
        union_query = exp.Union(this=union_query, expression=query, distinct=False)

    def _execute() -> dict[str, int]:
        with conn._safe_raw_sql(union_query) as cursor:  # type: ignore[attr-defined]
            rows = cursor.fetchall()

        return {str(dataset_name): int(row_count) for dataset_name, row_count in rows}

    return await asyncio.to_thread(_execute)


async def get_datasets_metadata(
    dataset_names: Sequence[str], schema_name: str
) -> dict[str, DatasetMetadata]:
    if not dataset_names:
        return {}

    dataset_list = list(dict.fromkeys(dataset_names))
    if not dataset_list:
        return {}

    conn = await get_connection()

    schemas = await _fetch_column_schemas(conn, dataset_list, schema_name)
    row_counts = await _fetch_row_counts(conn, list(schemas.keys()), schema_name)

    metadata: dict[str, DatasetMetadata] = {}

    for dataset_name in dataset_list:
        schema = schemas.get(dataset_name)
        row_count = row_counts.get(dataset_name)

        if not schema or row_count is None:
            continue

        metadata[dataset_name] = DatasetMetadata(
            schema=schema,
            row_count=row_count,
        )

    return metadata


async def get_dataset_metadata(
    dataset_name: str, schema_name: str
) -> DatasetMetadata | None:
    try:
        metadata = await get_datasets_metadata([dataset_name], schema_name)
    except TableNotFound:
        return None

    return metadata.get(dataset_name)
