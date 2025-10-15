import io
from typing import AsyncGenerator

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from ibis.common.exceptions import TableNotFound
from pydantic import BaseModel

from planar.data.exceptions import DatasetNotFoundError
from planar.data.utils import (
    get_dataset,
    get_dataset_metadata,
    get_datasets_metadata,
    list_datasets,
    list_schemas,
)
from planar.logging import get_logger
from planar.security.authorization import (
    DatasetAction,
    DatasetResource,
    validate_authorization_for,
)

logger = get_logger(__name__)


class DatasetMetadata(BaseModel):
    name: str
    table_schema: dict
    row_count: int


def create_dataset_router() -> APIRouter:
    router = APIRouter(tags=["Planar Datasets"])

    @router.get("/schemas", response_model=list[str])
    async def get_schemas():
        validate_authorization_for(
            DatasetResource(), DatasetAction.DATASET_LIST_SCHEMAS
        )
        schemas = await list_schemas()
        return schemas

    @router.get("/metadata", response_model=list[DatasetMetadata])
    async def list_planar_datasets(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        schema_name: str = Query("main"),
    ):
        validate_authorization_for(DatasetResource(), DatasetAction.DATASET_LIST)
        datasets = await list_datasets(limit, offset)

        dataset_names = [dataset.name for dataset in datasets]
        metadata_by_dataset = await get_datasets_metadata(dataset_names, schema_name)

        response = []
        for dataset in datasets:
            metadata = metadata_by_dataset.get(dataset.name)

            if not metadata:
                continue

            schema = metadata["schema"]
            row_count = metadata["row_count"]

            response.append(
                DatasetMetadata(
                    name=dataset.name,
                    row_count=row_count,
                    table_schema={
                        field_name: str(field_type)
                        for field_name, field_type in schema.items()
                    },
                )
            )

        return response

    @router.get("/metadata/{dataset_name}", response_model=DatasetMetadata)
    async def get_planar_dataset(dataset_name: str, schema_name: str = "main"):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_VIEW_DETAILS,
        )
        try:
            metadata = await get_dataset_metadata(dataset_name, schema_name)

            if not metadata:
                raise HTTPException(
                    status_code=404, detail=f"Dataset {dataset_name} not found"
                )

            schema = metadata["schema"]
            row_count = metadata["row_count"]

            return DatasetMetadata(
                name=dataset_name,
                row_count=row_count,
                table_schema={
                    field_name: str(field_type)
                    for field_name, field_type in schema.items()
                },
            )
        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    @router.get(
        "/content/{dataset_name}/arrow-stream", response_class=StreamingResponse
    )
    async def stream_dataset_content(
        dataset_name: str,
        batch_size: int = Query(100, ge=1, le=1000),
        limit: int | None = Query(None, ge=1),
    ):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_STREAM_CONTENT,
        )
        try:
            dataset = await get_dataset(dataset_name)

            # Apply limit parameter if specified
            table = await dataset.read(limit=limit)

            schema = table.schema().to_pyarrow()

            async def stream_content() -> AsyncGenerator[bytes, None]:
                sink = io.BytesIO()

                try:
                    with pa.ipc.new_stream(sink, schema) as writer:
                        yield sink.getvalue()  # yield the schema

                        batch_count = 0
                        for batch in table.to_pyarrow_batches(chunk_size=batch_size):
                            # reset the sink to only stream
                            # the current batch
                            # we don't want to stream the schema or previous
                            # batches again
                            sink.seek(0)
                            sink.truncate(0)

                            writer.write_batch(batch)
                            yield sink.getvalue()
                            batch_count += 1

                        # For empty datasets, ensure we have a complete stream
                        if batch_count == 0:
                            # Write an empty batch to ensure valid Arrow stream format
                            empty_batch = pa.RecordBatch.from_arrays(
                                [pa.array([], type=field.type) for field in schema],
                                schema=schema,
                            )
                            sink.seek(0)
                            sink.truncate(0)
                            writer.write_batch(empty_batch)
                            yield sink.getvalue()
                finally:
                    # Explicit BytesIO cleanup for memory safety
                    sink.close()

            return StreamingResponse(
                stream_content(),
                media_type="application/vnd.apache.arrow.stream",
                headers={
                    "Content-Disposition": f"attachment; filename={dataset_name}.arrow",
                    "X-Batch-Size": str(batch_size),
                    "X-Row-Limit": str(limit) if limit else "unlimited",
                },
            )
        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    @router.get("/content/{dataset_name}/download")
    async def download_dataset(dataset_name: str, schema_name: str = "main"):
        validate_authorization_for(
            DatasetResource(dataset_name=dataset_name),
            DatasetAction.DATASET_DOWNLOAD,
        )
        try:
            arrow_buffer = pa.BufferOutputStream()
            dataset = await get_dataset(dataset_name, schema_name)

            pyarrow_table = await dataset.to_pyarrow()

            pq.write_table(pyarrow_table, arrow_buffer)

            if arrow_buffer.tell() == 0:
                logger.warning(
                    "Dataset is empty",
                    dataset_name=dataset_name,
                    schema_name=schema_name,
                )

            buffer = arrow_buffer.getvalue()
            parquet_bytes = buffer.to_pybytes()
            bytes_io = io.BytesIO(parquet_bytes)

            return StreamingResponse(
                bytes_io,
                media_type="application/x-parquet",
                headers={
                    "Content-Disposition": f"attachment; filename={dataset_name}.parquet"
                },
            )
        except (DatasetNotFoundError, TableNotFound):
            raise HTTPException(
                status_code=404, detail=f"Dataset {dataset_name} not found"
            )

    return router
