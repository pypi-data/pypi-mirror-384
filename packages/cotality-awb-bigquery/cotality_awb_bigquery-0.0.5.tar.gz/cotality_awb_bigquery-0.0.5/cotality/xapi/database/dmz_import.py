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
"""Database-Agnostic DMZ Import Service

This import service works with any database that implements the DatabaseClient interface,
including Snowflake, Databricks, and BigQuery. It downloads data from cloud storage
via DMZ signed URLs and loads it into destination database tables with enhanced
FileDownloadResponse objects containing comprehensive statistics.
"""
from __future__ import annotations

import gc
import io
import logging
from typing import Callable, List

import pandas as pd
import requests
from pandas._typing import DtypeArg

from ...core.clgxtyping import CSVConfig, FileFormat
from ...core.exception import ClgxException, CommonErrorCodes
from ...core.interfaces.database import DatabaseClient
from ..dmz.client import DmzClient
from ..dmz.typing import FileDownloadRequest, FileDownloadResponse, SignedUrl

logger = logging.getLogger(__name__)


class DmzImport:
    """Database-agnostic DMZ Import service for large datasets via DMZ.

    This service works with any database that implements the DatabaseClient interface,
    including Snowflake, Databricks, and BigQuery. It uses the database client from
    the provided Platform instance and provides memory-optimized downloads from cloud
    storage via DMZ signed URLs.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        dmz_client: DmzClient,
        csv_config: CSVConfig = CSVConfig(),
        is_single_thread: bool = True,
    ):
        """Initialize the DMZ Export service.

        Args:
            database_client: DatabaseClient instance for executing queries
            dmz_client: DmzClient instance for generating signed URLs
            csv_config: Configuration for CSV exports (default: header=True, separator=',')
            is_single_thread: If True, use single-threaded processing (default: False)
        """
        self._database_client = database_client
        self._dmz_client = dmz_client
        self._csv_config = csv_config
        self._is_single_thread = is_single_thread

    def import_data(
        self,
        storage_id: str,
        base_path: str,
        data_types: DtypeArg | None,
        column_name_mapping: dict[str, str] | None,
        save_result_callback: Callable[[pd.DataFrame], None],
        download_format: FileFormat = FileFormat.CSV,
    ) -> FileDownloadResponse:
        """Import data from cloud storage using signed URLs via DMZ.

        This method downloads data from cloud storage files using signed URLs and
        loads the data into the specified destination table. It uses memory-optimized
        processing with concurrent workers to handle large datasets efficiently.

        Args:
            storage_id (str): Storage ID for cloud storage (e.g., "clip", "gs://bucket")
            base_path (str): Base path in the storage for files to download
            data_types (DtypeArg | None): Optional dictionary of column data types to load from CSV data file
            column_name_mapping (dict[str, str] | None): Optional mapping of column names from source to destination
            save_result_callback (Callable[[pd.DataFrame], None]): Callback function to process
            download_format (FileFormat, optional): Format of files to download. Defaults to CSV.
        Returns:
            FileDownloadResponse: Detailed download statistics and response data
        """
        dmz_request = FileDownloadRequest(storage_id=storage_id, path=base_path)

        # Generate signed URLs for the files to download
        dmz_download_response = self._dmz_client.get_signed_urls(dmz_request)

        # Download the data from the signed URLs
        file_download_response = FileDownloadResponse()
        self.single_thread_download(
            signed_urls=dmz_download_response.signed_urls,
            file_download_response=file_download_response,
            data_types=data_types,
            column_name_mapping=column_name_mapping,
            save_result_callback=save_result_callback,
            download_format=download_format,
        )

        return file_download_response

    def single_thread_download(
        self,
        signed_urls: List[SignedUrl],
        file_download_response: FileDownloadResponse,
        data_types: DtypeArg | None,
        column_name_mapping: dict[str, str] | None,
        save_result_callback: Callable[[pd.DataFrame], None],
        download_format: FileFormat,
    ) -> None:
        """Download data from signed URLs in a single-threaded manner.

        Args:
            signed_urls (List[SignedUrl]): List of signed URLs to download
            file_download_response (FileDownloadResponse): Response object containing signed URLs
            data_types (DtypeArg | None): Optional dictionary of column data types to
            column_name_mapping (dict[str, str] | None): Optional mapping of column names from source to destination
            save_result_callback (Callable[[pd.DataFrame], None]): Callback function to process
            download_format (FileFormat): Format of files to download

        Returns:
            List[Dict[str, Any]]: List of download responses with statistics
        """
        for signed_url in signed_urls:
            gc.collect()
            self._download_dataframe(
                signed_url=signed_url,
                file_download_response=file_download_response,
                data_types=data_types,
                column_name_mapping=column_name_mapping,
                save_result_callback=save_result_callback,
                download_format=download_format,
            )

    def _download_dataframe(
        self,
        signed_url: SignedUrl,
        file_download_response: FileDownloadResponse,
        data_types: DtypeArg | None,
        column_name_mapping: dict[str, str] | None,
        save_result_callback: Callable[[pd.DataFrame], None],
        download_format: FileFormat,
        request_timeout_in_seconds: int = 120,
    ) -> None:
        """Download a single file from a signed URL and return as a DataFrame.

        Args:
            signed_url (SignedUrl): Signed URL object containing the URL and metadata
            file_download_response (FileDownloadResponse): Response object to append download statistics
            data_types (DtypeArg | None): Optional dictionary of column data types to
            column_name_mapping (dict[str, str] | None): Optional mapping of column names from source to destination
            save_result_callback (Callable[[pd.DataFrame], None]): Callback function to process
            download_format (FileFormat): Format of the file to download
            request_timeout_in_seconds (int, optional): Timeout for the HTTP request in seconds. Defaults to 120.
        Returns:
        """
        try:
            response = self._download_file(
                signed_url=signed_url,
                request_timeout_in_seconds=request_timeout_in_seconds,
            )
            # Read content into memory
            content = response.content
            # Process based on file format
            if download_format == FileFormat.CSV:
                if data_types is None:
                    data_types = {}
                df = pd.read_csv(
                    io.BytesIO(content),
                    sep=self._csv_config.separator,
                    dtype=data_types,
                    header=0 if self._csv_config.header else None,
                )
            elif download_format == FileFormat.JSON:
                df = pd.read_json(io.BytesIO(content))
            elif download_format == FileFormat.PARQUET:
                df = pd.read_parquet(io.BytesIO(content))
            else:
                raise ClgxException(
                    error=CommonErrorCodes.GEN_INVALID_PARAMETER,
                    message=f"Unsupported format: {download_format.value}",
                )

            if column_name_mapping:
                unknown_columns = [
                    col for col in df.columns if col not in column_name_mapping
                ]
                if unknown_columns and len(unknown_columns) > 0:
                    logger.error(
                        "Unknown columns found in the CSV that are not in the expected schema: %s",
                        unknown_columns,
                    )
                    df = df.drop(columns=unknown_columns)
                df = df.rename(columns=column_name_mapping)

            save_result_callback(df)
        except ClgxException as err:
            raise err
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.GEN_RUN_TIME,
                message=f"Failed to download file from signed URL: {signed_url.url}",
                cause=err,
            ) from err

    def _download_file(
        self,
        signed_url: SignedUrl,
        request_timeout_in_seconds: int = 120,
    ) -> requests.Response:
        """Generate a download response dictionary with statistics.

        Args:
            signed_url (SignedUrl): Signed URL object containing the URL and metadata
            request_timeout_in_seconds (int, optional): Timeout for the HTTP request in seconds. Defaults to 120.

        Returns:
            Dict[str, Any]: Dictionary containing download statistics and metadata
        """
        for i in range(3):  # Retry up to 3 times
            try:
                response = requests.get(
                    signed_url.url, timeout=request_timeout_in_seconds, stream=True
                )
                if response.status_code == 200:
                    return response
                else:
                    logger.warning(
                        "Attempt %d: Failed to download file from signed URL: %s. HTTP status code: %d, Response: %s",
                        i + 1,
                        signed_url.url,
                        response.status_code,
                        response.text,
                    )
            except Exception as err:
                logger.warning(
                    "Attempt %d: Exception occurred while downloading file from signed URL: %s. Error: %s",
                    i + 1,
                    signed_url.url,
                    err,
                )
        raise ClgxException(
            error=CommonErrorCodes.API_SERVER_ERROR,
            message=f"Failed to download file from signed URL after 3 attempts: {signed_url.url}",
        )
