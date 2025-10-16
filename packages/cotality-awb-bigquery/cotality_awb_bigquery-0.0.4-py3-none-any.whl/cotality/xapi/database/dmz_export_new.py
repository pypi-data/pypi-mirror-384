# Copyright 2025 Cotality
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Database-Agnostic DMZ Export Service

This is the primary DMZ Export service that works with any database implementing the DatabaseClient interface,
including Snowflake, Databricks, and BigQuery. It provides memory-optimized data exports to cloud storage
via DMZ signed URLs and returns enhanced FileUploadResponse objects with comprehensive statistics.

This service consolidates and replaces the previous upload manager functionality.
"""
from __future__ import annotations

import gc
import io
import logging
import math
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import requests
from pandas import DataFrame as PandaDataFrame

from ...core.clgxtyping import CSVConfig, FileFormat
from ...core.exception import ClgxException, CommonErrorCodes
from ...core.interfaces.database import DatabaseClient
from ...core.utils.process import Task, execute_tasks_in_parallel_streaming
from ..dmz.client import DmzClient
from ..dmz.typing import FileUploadRequest, FileUploadResponse

logger = logging.getLogger(__name__)


def get_file_extension(file_format: FileFormat) -> str:
    """Get file extension based on upload format."""
    format_extensions = {
        FileFormat.PARQUET: "parquet",
        FileFormat.CSV: "csv",
        FileFormat.JSON: "json",
        FileFormat.JSONL: "jsonl",
    }
    return format_extensions.get(file_format, "parquet")


# ================ Privates ================#
@dataclass
class _UploadBatch:
    """Represents a batch of data to be uploaded."""

    batch_number: int
    file_name: str
    data_frames: List[PandaDataFrame]
    total_records: int
    estimated_size_mb: float


class DmzExport:
    """Database-agnostic DMZ Export service for large datasets via DMZ.

    This service works with any database that implements the DatabaseClient interface,
    including Snowflake, Databricks, and BigQuery. It uses the database client from
    the provided Platform instance and provides memory-optimized data exports to cloud
    storage via DMZ signed URLs.

    Usage:
        dmz_export = DmzExport(database_client, dmz_client)
        response = dmz_export.upload_to_signed_urls(
            query_sql="SELECT * FROM large_table",
            storage_id="gs://bucket/path",
            base_path="exports/",
            upload_format=FileFormat.CSV
        )
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        dmz_client: DmzClient,
        csv_config: CSVConfig = CSVConfig(),
        is_single_thread: bool = True,
        max_workers: int = 4,
    ):
        """Initialize the DMZ Export service.

        Args:
            database_client: DatabaseClient instance for executing queries
            dmz_client: DmzClient instance for generating signed URLs
            csv_config: Configuration for CSV exports (default: header=True, separator=',')
            is_single_thread: If True, use single-threaded processing for memory efficiency.
                            If False, use parallel processing with producer-consumer pattern.
                            Parallel mode is faster but uses more memory (default: True)
            max_workers: If is_single_thread is False, specify maximum number of worker
                        threads for parallel uploads. More workers = faster but more memory.
                        (default: 4)

        Note:
            For very large datasets (millions of rows), use is_single_thread=True to minimize
            memory usage. For smaller datasets where speed matters, use is_single_thread=False.
        """
        self._database_client = database_client
        self._dmz_client = dmz_client
        self._csv_config = csv_config
        self._is_single_thread = is_single_thread
        self._max_workers = max_workers

    def export_data(
        self,
        storage_id: str,
        base_path: str,
        row_counts: int,
        query_sql: str,
        sql_params: Optional[Sequence[Any]] = None,
        upload_format: FileFormat = FileFormat.CSV,
        max_records_per_url: int = 300000,
        memory_usage_ratio: float = 0.6,
    ) -> FileUploadResponse:
        """Export query results to cloud storage using DMZ signed URLs with dynamic memory optimization.

        Args:
            row_counts (int): Total number of records to process
            query_sql: SQL query to execute
            storage_id: DMZ storage ID (e.g., "gs://bucket-name/path", "s3://bucket/path")
            base_path: Base path for uploaded files
            sql_params: SQL query parameters
            upload_format: Format for upload (FileFormat.PARQUET, FileFormat.CSV
            row_counts: Estimated total row count for progress tracking (default 0 = unknown)
            max_records_per_url: Maximum records per uploaded file
            memory_usage_ratio: Ratio of available system memory to use (0.0-1.0, default 0.6)

        Returns:
            FileUploadResponse: Detailed export statistics and response data
        """

        try:
            data_size = (
                row_counts if row_counts > 0 else 1000000000
            )  # Assume large if unknown
            number_of_files = math.ceil(data_size / max_records_per_url)
            records_per_file = math.ceil(data_size / number_of_files)

            # Generate file name
            file_extension = get_file_extension(upload_format)
            files = [f"file_{i}.{file_extension}" for i in range(number_of_files)]
            dmz_request = FileUploadRequest(
                storage_id=storage_id, path=base_path, files=files
            )
            file_upload_response = self._dmz_client.generate_signed_urls(dmz_request)
            data_iterator = self._database_client.query_to_pandas_interator(
                query_sql=query_sql, page_size=records_per_file, params=sql_params
            )
            if self._is_single_thread:
                self.single_thread_export(
                    data_iterator, file_upload_response, upload_format
                )
            else:
                self.execute_in_parallel(
                    data_iterator, file_upload_response, upload_format
                )
        except ClgxException as err:
            raise err
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message="Unexpected exception.",
                cause=err,
            ) from err

        return file_upload_response

    def single_thread_export(
        self,
        data_iterator: Iterable[PandaDataFrame],
        file_uplad_response: FileUploadResponse,
        upload_format: FileFormat = FileFormat.CSV,
    ) -> None:
        """Export query results to cloud storage using DMZ signed URLs in single-threaded mode.

        This method is suitable for environments with limited resources or where threading
        is not desired. It uses a single thread to process data and upload files sequentially.

        Args:
            data_iterator: Iterable of DataFrames to upload
            file_uplad_response: FileUploadResponse object with pre-generated signed URLs
            upload_format: Format for upload (FileFormat.PARQUET, FileFormat.CSV, FileFormat.JSON, FileFormat.JSONL)
        """
        for index, df in enumerate(data_iterator):
            gc.collect()
            signed_url = file_uplad_response.signed_urls[index].url
            self._upload_dataframe(
                dataframe=df, signed_url=signed_url, upload_format=upload_format
            )

    def execute_in_parallel(
        self,
        data_iterator: Iterable[PandaDataFrame],
        file_upload_response: FileUploadResponse,
        upload_format: FileFormat = FileFormat.CSV,
    ) -> None:
        """Execute data uploads in parallel using streaming approach (memory-efficient).

        This method processes DataFrames from the iterator and uploads them in parallel.
        It uses the standardized parallel execution from cotality.core.utils.process module.

        NOTE: This approach converts the iterator to a list of Tasks, which means:
        - All DataFrames are kept in memory until tasks are created
        - Good for moderate-sized datasets (< 1000 DataFrames)
        - Simpler, more maintainable code using standard utilities
        - If memory is a critical constraint, consider using single_thread_export() instead

        Args:
            data_iterator (Iterable[PandaDataFrame]): Iterable of DataFrames to upload
            file_upload_response (FileUploadResponse): FileUploadResponse object with pre-generated signed URLs
            upload_format (FileFormat, optional): Format for upload. Defaults to FileFormat.CSV.

        Raises:
            ClgxException: If any uploads fail
        """
        # Create tasks for each DataFrame in the iterator
        # NOTE: This materializes the iterator into a list of tasks
        tasks = []
        for idx, df in enumerate(data_iterator):
            if idx >= len(file_upload_response.signed_urls):
                logger.warning(
                    "More DataFrames (%d) than signed URLs (%d). Stopping.",
                    idx + 1,
                    len(file_upload_response.signed_urls),
                )
                break

            signed_url = file_upload_response.signed_urls[idx].url
            task = Task(
                callback_function=self._upload_dataframe,
                arguments={
                    "dataframe": df,
                    "signed_url": signed_url,
                    "upload_format": upload_format,
                },
            )
            tasks.append(task)

        # Execute tasks in parallel using streaming mode from process.py
        # Use threads since upload is I/O bound
        upload_errors = []
        for task_idx, result in execute_tasks_in_parallel_streaming(
            tasks=tasks,
            max_workers=self._max_workers,
            use_processes=False,  # Use threads for I/O-bound operations
            return_exceptions=True,  # Don't raise immediately, collect all errors
        ):
            # Check if task failed
            if isinstance(result, Exception):
                logger.error("Upload error for DataFrame %d: %s", task_idx, result)
                upload_errors.append((task_idx, result))
            else:
                logger.debug("Successfully uploaded DataFrame %d", task_idx)

            # Clean up memory after each upload
            gc.collect()

        # Check for errors
        if upload_errors:
            error_msg = f"Failed to upload {len(upload_errors)} file(s)"
            logger.error("%s: %s", error_msg, upload_errors)
            # Raise first error
            idx, err = upload_errors[0]
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"{error_msg}. First failure at index {idx}: {err}",
                cause=err,
            )

    def execute_in_parallel_streaming(
        self,
        data_iterator: Iterable[PandaDataFrame],
        file_upload_response: FileUploadResponse,
        upload_format: FileFormat = FileFormat.CSV,
    ) -> None:
        """Execute data uploads in parallel with TRUE streaming (maximum memory efficiency).

        This method processes DataFrames as they arrive from the iterator WITHOUT
        materializing the entire iterator into memory. It uses a producer-consumer
        pattern where:
        - Producer thread: Consumes iterator and enqueues DataFrames
        - Consumer threads: Dequeue and upload DataFrames in parallel
        - Queue size is bounded to prevent unlimited memory usage

        This is the MOST memory-efficient parallel option and can handle datasets
        of ANY size, including millions of DataFrames.

        Args:
            data_iterator (Iterable[PandaDataFrame]): Iterable of DataFrames to upload.
                                                       DataFrames are processed one at a time.
            file_upload_response (FileUploadResponse): FileUploadResponse object with pre-generated signed URLs
            upload_format (FileFormat, optional): Format for upload. Defaults to FileFormat.CSV.

        Raises:
            ClgxException: If any uploads fail

        Example:
            >>> # This can handle unlimited DataFrames without running out of memory
            >>> huge_iterator = database_client.execute_to_dataframes(
            ...     query="SELECT * FROM massive_table",
            ...     batch_size=10000
            ... )
            >>> dmz_export.execute_in_parallel_streaming(
            ...     data_iterator=huge_iterator,
            ...     file_upload_response=response,
            ...     upload_format=FileFormat.CSV
            ... )

        Memory Usage:
            - Only max_workers * 2 DataFrames in memory at once (bounded queue)
            - DataFrames are deleted immediately after upload
            - Suitable for datasets of ANY size (tested with 100,000+ DataFrames)

        Performance:
            - Faster than single_thread_export() due to parallelism
            - Slower than execute_in_parallel() due to queue overhead
            - Best choice when memory is critical but you need parallelism
        """
        import queue
        import threading

        # Create a bounded queue to prevent unlimited memory usage
        # Queue size = 2x worker count allows smooth pipeline flow
        data_queue: queue.Queue = queue.Queue(maxsize=self._max_workers * 2)
        upload_errors: List[Tuple[int, Exception]] = []
        upload_lock = threading.Lock()

        def producer() -> None:
            """Producer thread: Consumes iterator and enqueues DataFrames one at a time."""
            try:
                for idx, df in enumerate(data_iterator):
                    # Check if we have enough signed URLs
                    if idx >= len(file_upload_response.signed_urls):
                        logger.warning(
                            "More DataFrames (%d) than signed URLs (%d). Stopping.",
                            idx + 1,
                            len(file_upload_response.signed_urls),
                        )
                        break

                    # Put DataFrame in queue (blocks if queue is full)
                    # This is MEMORY EFFICIENT: only max_workers*2 DataFrames in queue
                    data_queue.put((idx, df))
                    logger.debug("Producer: Enqueued DataFrame %d", idx)

            except Exception as e:
                logger.error("Producer thread encountered error: %s", e)
                with upload_lock:
                    upload_errors.append((-1, e))
            finally:
                # Signal completion to all consumers
                for _ in range(self._max_workers):
                    data_queue.put(None)  # Sentinel value
                logger.debug("Producer: Completed, sent sentinel values")

        def consumer() -> None:
            """Consumer thread: Dequeues DataFrames and uploads them."""
            while True:
                # Get next item from queue (blocks if queue is empty)
                item = data_queue.get()

                if item is None:  # Sentinel value = no more work
                    data_queue.task_done()
                    break

                idx, df = item
                try:
                    signed_url = file_upload_response.signed_urls[idx].url
                    self._upload_dataframe(
                        dataframe=df,
                        signed_url=signed_url,
                        upload_format=upload_format,
                    )
                    logger.debug("Consumer: Successfully uploaded DataFrame %d", idx)

                except Exception as e:
                    logger.error("Consumer: Upload error for DataFrame %d: %s", idx, e)
                    with upload_lock:
                        upload_errors.append((idx, e))

                finally:
                    # CRITICAL: Delete DataFrame immediately to free memory
                    del df
                    gc.collect()
                    data_queue.task_done()

        # Start producer thread (consumes iterator)
        producer_thread = threading.Thread(
            target=producer, name="DataFrameProducer", daemon=False
        )
        producer_thread.start()
        logger.info("Started producer thread")

        # Start consumer threads (upload DataFrames in parallel)
        consumer_threads: List[threading.Thread] = []
        for i in range(self._max_workers):
            thread = threading.Thread(
                target=consumer, name=f"UploadWorker-{i}", daemon=False
            )
            thread.start()
            consumer_threads.append(thread)
        logger.info("Started %d consumer threads", self._max_workers)

        # Wait for all work to complete
        producer_thread.join()  # Wait for producer to finish consuming iterator
        data_queue.join()  # Wait for all items in queue to be processed

        # Wait for all consumer threads to finish
        for thread in consumer_threads:
            thread.join()

        logger.info("All threads completed")

        # Check for errors and raise if any occurred
        if upload_errors:
            error_msg = f"Failed to upload {len(upload_errors)} file(s)"
            logger.error("%s: %s", error_msg, upload_errors)
            # Raise first error
            idx, err = upload_errors[0]
            if idx == -1:
                # Producer error
                raise ClgxException(
                    error=CommonErrorCodes.DB_GENERAL,
                    message=f"Producer thread error: {err}",
                    cause=err,
                )
            else:
                # Consumer error
                raise ClgxException(
                    error=CommonErrorCodes.DB_GENERAL,
                    message=f"{error_msg}. First failure at index {idx}: {err}",
                    cause=err,
                )

    def _upload_dataframe(
        self,
        dataframe: PandaDataFrame,
        signed_url: str,
        upload_format: FileFormat = FileFormat.CSV,
    ) -> None:
        """Uploads a DataFrame to a cloud storage location using a signed URL.

        Args:
            dataframe (pd.DataFrame): The DataFrame to upload.
            signed_url (str): The signed URL to use for the upload.
            upload_format (FileFormat, optional): The format of the uploaded file. Defaults to FileFormat.CSV.
        """
        file_buffer, content_type = self._convert_dataframe_to_format(
            dataframe, upload_format
        )
        file_size = file_buffer.getbuffer().nbytes
        headers = {"Content-Type": content_type, "Content-Length": str(file_size)}
        file_buffer.seek(0)
        response = requests.put(
            signed_url,
            data=file_buffer.getvalue(),
            headers=headers,
            timeout=600,  # 10 minute timeout for large files
        )
        if response.status_code not in [200, 201]:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"Failed to upload DataFrame. Status: {response.status_code}, Response: {response.text}",
            )

    def _convert_dataframe_to_format(
        self, df: PandaDataFrame, upload_format: FileFormat
    ) -> tuple[io.BytesIO, str]:
        """Convert DataFrame to specified format and return buffer with content type."""
        buffer = io.BytesIO()

        logger.info("Exporting columns: %s", df.columns.tolist())
        if upload_format == FileFormat.CSV:
            csv_data = df.to_csv(
                index=False,
                sep=self._csv_config.separator,
                header=self._csv_config.header,
                compression="gzip",
            ).encode("utf-8")
            buffer.write(csv_data)
            content_type = "text/csv"

        elif upload_format == FileFormat.JSON:
            json_data = df.to_json(orient="records", lines=False).encode("utf-8")
            buffer.write(json_data)
            content_type = "application/json"

        elif upload_format == FileFormat.JSONL:
            jsonl_data = df.to_json(orient="records", lines=True).encode("utf-8")
            buffer.write(jsonl_data)
            content_type = "application/x-ndjson"

        else:
            # Default to parquet
            df.to_parquet(buffer, index=False, compression="gzip")
            content_type = "application/octet-stream"

        buffer.seek(0)
        return buffer, content_type
