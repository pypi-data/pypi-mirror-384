"""Configuration for Planar data module."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from planar.files.storage.config import StorageConfig


class PostgresCatalogConfig(BaseModel):
    """Configuration for PostgreSQL catalog backend."""

    type: Literal["postgres"]
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    db: str

    model_config = ConfigDict(frozen=True)


class SQLiteCatalogConfig(BaseModel):
    """Configuration for SQLite catalog backend."""

    type: Literal["sqlite"]
    path: str  # Path to .sqlite file

    model_config = ConfigDict(frozen=True)


# Discriminated union for catalog configurations
CatalogConfig = Annotated[
    PostgresCatalogConfig | SQLiteCatalogConfig,
    Field(discriminator="type"),
]


class DataConfig(BaseModel):
    """Configuration for data features."""

    catalog: CatalogConfig
    storage: StorageConfig  # Reuse existing StorageConfig from files

    # Optional settings
    catalog_name: str = "planar_data"  # Default catalog name in Ducklake

    model_config = ConfigDict(frozen=True)

    def is_sqlite_catalog(self) -> bool:
        return self.catalog.type == "sqlite"
