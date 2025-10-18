from __future__ import annotations
import json
import math
import os
from pathlib import Path
from typing import List, Literal, TYPE_CHECKING

from adaptive_sdk.graphql_client import (
    DatasetCreate,
    Upload,
    LoadDatasetCreateDataset,
    ListDatasetsDatasets,
    DatasetData,
    DatasetCreateFromMultipartUpload,
)
from adaptive_sdk.graphql_client.custom_mutations import Mutation
from adaptive_sdk.graphql_client.custom_fields import DatasetFields
from adaptive_sdk.rest import rest_types
from adaptive_sdk.error_handling import rest_error_handler

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive

MIN_CHUNK_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_CHUNK_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
MAX_PARTS_COUNT = 10000


def _calculate_upload_parts(file_size: int) -> tuple[int, int]:
    """
    Calculate optimal number of parts and chunk size for multipart upload.

    Strategy: Scale chunk size based on file size for optimal performance

    Args:
        file_size: Size of the file in bytes

    Returns:
        Tuple of (total_parts, chunk_size_bytes)

    Raises:
        ValueError: If file is too large to upload with the given constraints
    """
    if file_size < MIN_CHUNK_SIZE_BYTES:
        raise ValueError(f"File size ({file_size:,} bytes) is too small for chunked upload")

    # Select appropriate chunk size based on file size
    SIZE_500MB = 500 * 1024 * 1024
    SIZE_10GB = 10 * 1024 * 1024 * 1024
    SIZE_50GB = 50 * 1024 * 1024 * 1024

    if file_size < SIZE_500MB:
        chunk_size = 5 * 1024 * 1024  # 5MB
    elif file_size < SIZE_10GB:
        chunk_size = 10 * 1024 * 1024  # 10MB
    elif file_size < SIZE_50GB:
        chunk_size = 50 * 1024 * 1024  # 50MB
    else:
        chunk_size = 100 * 1024 * 1024  # 100MB

    total_parts = math.ceil(file_size / chunk_size)

    if total_parts > MAX_PARTS_COUNT:
        # Calculate minimum chunk size needed to stay under max parts
        chunk_size = math.ceil(file_size / MAX_PARTS_COUNT)

        # Check if we exceed max chunk size
        if chunk_size > MAX_CHUNK_SIZE_BYTES:
            max_file_size = MAX_CHUNK_SIZE_BYTES * MAX_PARTS_COUNT
            raise ValueError(
                f"File size ({file_size:,} bytes) exceeds maximum uploadable size "
                f"({max_file_size:,} bytes = {MAX_PARTS_COUNT} parts * {MAX_CHUNK_SIZE_BYTES:,} bytes)"
            )

        total_parts = math.ceil(file_size / chunk_size)

    return total_parts, chunk_size


class Datasets(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with file datasets.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def upload(
        self,
        file_path: str,
        dataset_key: str,
        name: str | None = None,
        use_case: str | None = None,
    ) -> LoadDatasetCreateDataset:
        """
         Upload a dataset from a file. File must be jsonl, where each line should match structure in example below.

        Args:
            file_path: Path to jsonl file.
            dataset_key: New dataset key.
            name: Optional name to render in UI; if `None`, defaults to same as `dataset_key`.

        Example:
        ```
        {"messages": [{"role": "system", "content": "<optional system prompt>"}, {"role": "user", "content": "<user content>"}, {"role": "assistant", "content": "<assistant answer>"}], "completion": "hey"}
        ```
        """
        file_size = os.path.getsize(file_path)

        if file_size > MIN_CHUNK_SIZE_BYTES:
            return self._chunked_upload(file_path, dataset_key, name, use_case)
        else:
            # Use standard GraphQL upload for smaller files
            input = DatasetCreate(
                useCase=self.use_case_key(use_case),
                name=name if name else dataset_key,
                key=dataset_key,
            )
            filename = Path(file_path).stem
            with open(file_path, "rb") as f:
                file_upload = Upload(
                    filename=filename, content=f, content_type="application/jsonl"
                )
                return self._gql_client.load_dataset(
                    input=input, file=file_upload
                ).create_dataset

    def _chunked_upload(
        self,
        file_path: str,
        dataset_key: str,
        name: str | None = None,
        use_case: str | None = None,
    ) -> LoadDatasetCreateDataset:
        """Upload large files using chunked upload via REST API."""
        file_size = os.path.getsize(file_path)
        total_parts, chunk_size = _calculate_upload_parts(file_size)

        # Step 1: Initialize chunked upload session
        init_request = rest_types.InitChunkedUploadRequest(
            content_type="application/jsonl",
            metadata=None,
            total_parts_count=total_parts,
        )
        response = self._rest_client.post(
            "/upload/init", json=init_request.model_dump()
        )
        rest_error_handler(response)
        init_response = rest_types.InitChunkedUploadResponse.model_validate(
            response.json()
        )
        session_id = init_response.session_id

        try:
            # Step 2: Upload each part
            with open(file_path, "rb") as f:
                for part_number in range(1, total_parts + 1):
                    chunk_data = f.read(chunk_size)

                    response = self._rest_client.post(
                        "/upload/part",
                        params={"session_id": session_id, "part_number": part_number},
                        content=chunk_data,
                        headers={"Content-Type": "application/octet-stream"},
                    )
                    rest_error_handler(response)

            # Step 3: Finalize upload by creating dataset from multipart upload
            input = DatasetCreateFromMultipartUpload(
                useCase=self.use_case_key(use_case),
                name=name if name else dataset_key,
                key=dataset_key,
                uploadSessionId=session_id,
            )

            mutation_field = Mutation.create_dataset_from_multipart_upload(input=input)
            mutation_field.fields(
                DatasetFields.id,
                DatasetFields.key,
                DatasetFields.name,
                DatasetFields.created_at,
                DatasetFields.kind,
                DatasetFields.records,
            )
            result = self._gql_client.mutation(
                mutation_field, operation_name="CreateDatasetFromMultipartUpload"
            )
            return LoadDatasetCreateDataset.model_validate(
                result["createDatasetFromMultipartUpload"]
            )

        except Exception as e:
            # Abort the upload session on error
            try:
                abort_request = rest_types.AbortChunkedUploadRequest(
                    session_id=session_id
                )
                # delete with body works in runtime but not in type checking
                self._rest_client.delete(  # type: ignore[call-arg]
                    "/upload/abort",
                    content=json.dumps(abort_request.model_dump()),
                    headers={"Content-Type": "application/json"},
                )
            except Exception:
                pass  # Best effort cleanup
            raise

    def list(
        self,
        use_case: str | None = None,
    ) -> List[ListDatasetsDatasets]:
        """
        List previously uploaded datasets.
        """
        return self._gql_client.list_datasets(self.use_case_key(use_case)).datasets

    def get(self, key: str, use_case: str | None = None) -> DatasetData | None:
        """
        Get details for dataset.

        Args:
            key: Dataset key.
        """
        return self._gql_client.describe_dataset(
            key, self.use_case_key(use_case)
        ).dataset

    def delete(self, key: str, use_case: str | None = None) -> bool:
        """Delete dataset."""
        return self._gql_client.delete_dataset(
            id_or_key=key, use_case=self.use_case_key(use_case)
        ).delete_dataset


class AsyncDatasets(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def upload(
        self,
        file_path: str,
        dataset_key: str,
        name: str | None = None,
        use_case: str | None = None,
    ) -> LoadDatasetCreateDataset:
        """
        Upload a dataset from a file. File must be jsonl, where each line should match structure in example below.

        Args:
            file_path: Path to jsonl file.
            dataset_key: New dataset key.
            name: Optional name to render in UI; if `None`, defaults to same as `dataset_key`.

        Example:
        ```
        {"messages": [{"role": "system", "content": "<optional system prompt>"}, {"role": "user", "content": "<user content>"}, {"role": "assistant", "content": "<assistant answer>"}], "completion": "hey"}
        ```
        """
        file_size = os.path.getsize(file_path)

        # Use chunked upload for files larger than MIN_CHUNK_SIZE_BYTES
        if file_size > MIN_CHUNK_SIZE_BYTES:
            return await self._chunked_upload(file_path, dataset_key, name, use_case)
        else:
            # Use standard GraphQL upload for smaller files
            input = DatasetCreate(
                useCase=self.use_case_key(use_case),
                name=name if name else dataset_key,
                key=dataset_key,
            )
            filename = Path(file_path).stem
            with open(file_path, "rb") as f:
                file_upload = Upload(
                    filename=filename, content=f, content_type="application/jsonl"
                )
                upload_result = await self._gql_client.load_dataset(
                    input=input, file=file_upload
                )
                return upload_result.create_dataset

    async def _chunked_upload(
        self,
        file_path: str,
        dataset_key: str,
        name: str | None = None,
        use_case: str | None = None,
    ) -> LoadDatasetCreateDataset:
        """Upload large files using chunked upload via REST API."""
        file_size = os.path.getsize(file_path)
        total_parts, chunk_size = _calculate_upload_parts(file_size)

        # Step 1: Initialize chunked upload session
        init_request = rest_types.InitChunkedUploadRequest(
            content_type="application/jsonl",
            metadata=None,
            total_parts_count=total_parts,
        )
        response = await self._rest_client.post(
            "/upload/init", json=init_request.model_dump()
        )
        rest_error_handler(response)
        init_response = rest_types.InitChunkedUploadResponse.model_validate(
            response.json()
        )
        session_id = init_response.session_id

        try:
            # Step 2: Upload each part
            with open(file_path, "rb") as f:
                for part_number in range(1, total_parts + 1):
                    chunk_data = f.read(chunk_size)

                    response = await self._rest_client.post(
                        "/upload/part",
                        params={"session_id": session_id, "part_number": part_number},
                        content=chunk_data,
                        headers={"Content-Type": "application/octet-stream"},
                    )
                    rest_error_handler(response)

            input = DatasetCreateFromMultipartUpload(
                useCase=self.use_case_key(use_case),
                name=name if name else dataset_key,
                key=dataset_key,
                uploadSessionId=session_id,
            )

            mutation_field = Mutation.create_dataset_from_multipart_upload(input=input)
            mutation_field.fields(
                DatasetFields.id,
                DatasetFields.key,
                DatasetFields.name,
                DatasetFields.created_at,
                DatasetFields.kind,
                DatasetFields.records,
            )
            result = await self._gql_client.mutation(
                mutation_field, operation_name="CreateDatasetFromMultipartUpload"
            )
            return LoadDatasetCreateDataset.model_validate(
                result["createDatasetFromMultipartUpload"]
            )

        except Exception as e:
            # Abort the upload session on error
            try:
                abort_request = rest_types.AbortChunkedUploadRequest(
                    session_id=session_id
                )
                # delete with body works in runtime but not in type checking
                await self._rest_client.delete(  # type: ignore[call-arg]
                    "/upload/abort",
                    content=json.dumps(abort_request.model_dump()),
                    headers={"Content-Type": "application/json"},
                )
            except Exception:
                pass
            raise

    async def list(
        self,
        use_case: str | None = None,
    ) -> List[ListDatasetsDatasets]:
        """
        List previously uploaded datasets.
        """
        results = await self._gql_client.list_datasets(self.use_case_key(use_case))
        return results.datasets

    async def get(self, key: str, use_case: str | None = None) -> DatasetData | None:
        """
        Get details for dataset.

        Args:
            key: Dataset key.
        """
        result = await self._gql_client.describe_dataset(
            key, self.use_case_key(use_case)
        )
        return result.dataset

    async def delete(self, key: str, use_case: str | None = None) -> bool:
        """Delete dataset."""
        return (
            await self._gql_client.delete_dataset(
                id_or_key=key, use_case=self.use_case_key(use_case)
            )
        ).delete_dataset
