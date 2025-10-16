"""PlanarDataset implementation for working with Ducklake tables."""

import asyncio
from typing import Literal, Self

import ibis
import polars as pl
import pyarrow as pa
from ibis.backends.duckdb import Backend as DuckDBBackend
from ibis.common.exceptions import TableNotFound
from pydantic import BaseModel

from planar.data.connection import get_connection
from planar.logging import get_logger

from .exceptions import DataError, DatasetAlreadyExistsError, DatasetNotFoundError

logger = get_logger(__name__)


class PlanarDataset(BaseModel):
    """Reference to a Ducklake table.

    This class provides a simple interface for working with datasets in Ducklake,
    handling creation, reading, writing, and deletion of tabular data.
    """

    # TODO: Add support for schema name (ie. namespace)
    name: str  # Table name in Ducklake
    # TODO: Add snapshot version: no version = latest, otherwise time travel on read operations
    # TODO: Add partition support? A Dataset representation could be a table with a partition column

    is_planar_dataset: bool = True

    model_config = {"arbitrary_types_allowed": True}
    # TODO: Add serialization metadata to make clear this is a dataset reference
    # like EntityField.

    @classmethod
    async def create(cls, name: str, if_not_exists: bool = True) -> Self:
        """Create a dataset reference.

        Note: The actual table is created when data is first written to avoid
        DuckDB's requirement that tables have at least one column.

        Args:
            name: Name of the dataset
            if_not_exists: If True, don't raise error if dataset exists. default: True
            catalog: Catalog name in Ducklake

        Returns:
            PlanarDataset instance

        Raises:
            DatasetAlreadyExistsError: If dataset exists and if_not_exists=False
        """
        dataset = cls(name=name)

        # Check if dataset already exists
        if await dataset.exists():
            if not if_not_exists:
                raise DatasetAlreadyExistsError(f"Dataset {name} already exists")
            logger.debug("dataset already exists", dataset_name=name)
        else:
            logger.debug("dataset reference created", dataset_name=name)

        return dataset

    async def exists(self) -> bool:
        """Check if the dataset exists in Ducklake."""
        con = await get_connection()
        return await self._table_exists(con)

    async def _table_exists(self, con: DuckDBBackend) -> bool:
        """Check for table existence using the provided connection."""

        try:
            # TODO: Query for the table name directly
            tables = await asyncio.to_thread(con.list_tables)
            return self.name in tables
        except Exception as e:
            logger.warning("failed to check dataset existence", error=str(e))
            return False

    async def write(
        self,
        data: pl.DataFrame | pl.LazyFrame | ibis.Table | list | dict,
        mode: Literal["overwrite", "append"] = "append",
    ) -> None:
        """Write data to the dataset.

        Args:
            data: Data to write (Polars DataFrame/LazyFrame, PyArrow Table, or Ibis expression)
            mode: Write mode - "append" or "overwrite"
        """
        overwrite = mode == "overwrite"

        try:
            con = await get_connection()
            table_exists = await self._table_exists(con)

            if not table_exists:
                await asyncio.to_thread(
                    con.create_table, self.name, data, overwrite=overwrite
                )
            else:
                # TODO: Explore if workflow context can be used to set metadata
                # on the snapshot version for lineage
                if isinstance(data, (pl.DataFrame, pl.LazyFrame)):
                    await asyncio.to_thread(
                        con.insert,
                        self.name,
                        ibis.memtable(data),
                        overwrite=overwrite,
                    )
                else:
                    await asyncio.to_thread(
                        con.insert, self.name, data, overwrite=overwrite
                    )

            logger.debug(
                "wrote data to dataset",
                dataset_name=self.name,
                mode=mode,
            )
        except Exception as e:
            raise DataError(f"Failed to write data: {e}") from e

    async def read(
        self,
        columns: list[str] | None = None,
        limit: int | None = None,
    ) -> ibis.Table:
        """Read data as an Ibis table expression.

        Args:
            columns: Optional list of columns to select
            limit: Optional row limit

        Returns:
            Ibis table expression that can be further filtered using Ibis methods
        """
        try:
            con = await get_connection()
            table = await asyncio.to_thread(con.table, self.name)

            if columns:
                table = table.select(columns)

            if limit:
                table = table.limit(limit)

            return table
        except TableNotFound as e:
            raise DatasetNotFoundError(f"Dataset {self.name} not found") from e
        except Exception as e:
            raise DataError(f"Failed to read data: {e}") from e

    async def to_polars(self) -> pl.DataFrame:
        """Read entire dataset as Polars DataFrame."""
        table = await self.read()
        return await asyncio.to_thread(table.to_polars)

    async def to_pyarrow(self) -> pa.Table:
        """Read entire dataset as PyArrow Table."""
        table = await self.read()
        return await asyncio.to_thread(table.to_pyarrow)

    async def delete(self) -> None:
        """Delete the dataset."""
        try:
            con = await get_connection()
            await asyncio.to_thread(con.drop_table, self.name, force=True)
            logger.info("deleted dataset", dataset_name=self.name)
        except Exception as e:
            raise DataError(f"Failed to delete dataset: {e}") from e
