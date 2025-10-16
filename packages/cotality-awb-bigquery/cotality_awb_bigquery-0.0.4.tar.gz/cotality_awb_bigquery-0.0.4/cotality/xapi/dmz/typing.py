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
"""DMZ File API"""
from __future__ import annotations

import enum
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import DataClassJsonMixin

from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from ...core.utils.dict import dict_snake_case

logger = logging.getLogger(__name__)

DMZ_API = "/signed-urls"


@dataclass(init=True, frozen=False)
class SignedUrl(DataClassJsonMixin):
    """Represents a signed URL for clip upload/download."""

    file: str = ""
    url: str = ""


@dataclass(init=True, frozen=False)
class FileUploadRequest(DataClassJsonMixin):
    """Request for file upload.

    Args:
        job_id (str): Job ID for the clip lookup
        status_code (int): HTTP status code
        api (str): API endpoint used
        request_id (str): Request ID for tracking
        response_id (str): Response ID for tracking
        output_counts (int): Number of outputs processed
        message (str): Message from the API response
    """

    storage_id: str = ""
    path: str = ""
    files: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(init=True, frozen=False)
class FileUploadResponse(DataClassJsonMixin):
    """Response for file upload with upload statistics."""

    # DMZ response fields
    url_prefix: str = ""  # gs://<storage_id_path>/<organization>/<app>
    location_prefix: str = ""
    signed_urls: list[SignedUrl] = field(default_factory=list)
    storage_prefix: str = ""  # Random path: <path_id>

    # Upload statistics fields (from UploadStats)
    total_pages_processed: int = 0
    total_records: int = 0
    total_files_uploaded: int = 0
    total_bytes_uploaded: int = 0
    upload_errors: int = 0
    start_time: float = 0
    end_time: float = 0
    current_memory_mb: float = 0
    peak_memory_mb: float = 0
    uploaded_files: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        """Calculate total duration of the upload process."""
        return self.end_time - self.start_time if self.end_time > self.start_time else 0

    @property
    def records_per_second(self) -> float:
        """Calculate records processed per second."""
        return (
            self.total_records / self.total_duration if self.total_duration > 0 else 0
        )

    @property
    def mb_per_second(self) -> float:
        """Calculate megabytes uploaded per second."""
        mb_uploaded = self.total_bytes_uploaded / 1024 / 1024
        return mb_uploaded / self.total_duration if self.total_duration > 0 else 0

    @property
    def avg_records_per_file(self) -> float:
        """Calculate average records per uploaded file."""
        return (
            self.total_records / self.total_files_uploaded
            if self.total_files_uploaded > 0
            else 0
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total_attempts = self.total_files_uploaded + self.upload_errors
        return (
            (self.total_files_uploaded / total_attempts * 100)
            if total_attempts > 0
            else 0
        )

    # TO-DO: Remove this once we have new DMZ API in place.
    def post_init(self, file_upload_request: FileUploadRequest):
        """Post-initialization method to set URL prefixes.
        This method is called only if url_prefix is not set, old API response.
        New response should contains both url_prefix and location_prefix.

        Args:
            self (FileUploadResponse): The current instance of FileUploadResponse
            file_upload_request (FileUploadRequest): The original file upload request
        """
        # location_prefix = gs://<storage_id_path>/<organization>/<app>/<path_id>/<request_path>
        # <storage_id> = gs://idap_uat_clip_property_portfolio_management/dmz/clip
        # <organization> = usbank
        # <app> = snowflake-clip
        # <path_id> = c435ccb6-293c-491f-89f5-3f81f2c69694
        # <request_path> = mp_api/clip/c541e0a9623e4149b7958a33b96599e5/e84ce11f409d41a0aef49715bc1f2e8b/input

        # url_prefix is not set, so try to exract from location_prefix
        if not self.url_prefix:
            prefix = self.location_prefix[
                : self.location_prefix.rfind(file_upload_request.path)
            ]
            prefix = prefix.rstrip("/")
            path_id_index = prefix.rfind("/")
            self.storage_prefix = prefix[path_id_index + 1 :]
            self.url_prefix = prefix[:path_id_index]

    @classmethod
    def extract_from_dict(cls, text_data: str) -> FileUploadResponse:
        """Create an instance from JSON data.

        Args:
            data (str): Response text data

        Returns:
            FileUploadResponse: An instance of FileUploadResponse
        """
        try:
            data = dict_snake_case(json.loads(text_data))
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f"Failed to parse JSON: {text_data}",
                cause=e,
            ) from e

        if (
            not data.get("location_prefix")
            or not (files := data.get("files"))
            or not (file := files[0])
            or not file.get("url")
            or not file.get("file")
        ):
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f'Expected "location_prefix", "files(file,url)" in response, got: {data}',
            )
        instance = cls()
        instance.url_prefix = data.get("url_prefix", "")
        instance.location_prefix = data["location_prefix"]
        files = data["files"]
        if not isinstance(files, list):
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f'Expected "files" to be a list, got type: {type(files)}. Value: {files}',
            )
        instance.signed_urls = [SignedUrl.from_dict(signed_url) for signed_url in files]
        return instance


@dataclass(init=True, frozen=False)
class FileDownloadRequest(DataClassJsonMixin):
    """Request for file download."""

    storage_id: str = ""
    path: str = ""


@dataclass(init=True, frozen=False)
class FileDownloadResponse(DataClassJsonMixin):
    """Response for file download with enhanced statistics.

    This class combines DMZ signed URL response data with comprehensive download statistics,
    providing detailed metrics about the import operation.
    """

    # DMZ response data
    signed_urls: list[SignedUrl] = field(default_factory=list)

    # Download statistics
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    files_processed: int = 0
    total_files: int = 0
    rows_processed: int = 0
    bytes_downloaded: int = 0
    failed_files: list[str] = field(default_factory=list)
    _lock: Any = field(default_factory=lambda: None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the lock after object creation."""
        if self._lock is None:
            self._lock = threading.Lock()

    def record_file_completed(self, file_path: str, rows: int, size_bytes: int) -> None:
        """Record completion of a file download."""
        if self._lock is None:
            self._lock = threading.Lock()
        with self._lock:
            self.files_processed += 1
            self.rows_processed += rows
            self.bytes_downloaded += size_bytes

    def record_file_failed(self, file_path: str) -> None:
        """Record failure of a file download."""
        if self._lock is None:
            self._lock = threading.Lock()
        with self._lock:
            self.failed_files.append(file_path)

    def finalize(self) -> None:
        """Mark the download operation as complete."""
        self.end_time = time.time()

    def duration(self) -> float:
        """Get the duration of the download operation."""
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of file downloads."""
        if self.total_files == 0:
            return 0.0
        return (self.files_processed / self.total_files) * 100.0

    @property
    def failed_count(self) -> int:
        """Get the number of failed downloads."""
        return len(self.failed_files)

    @property
    def files_per_second(self) -> float:
        """Calculate files processed per second."""
        duration = self.duration()
        if duration == 0:
            return 0.0
        return self.files_processed / duration

    @property
    def rows_per_second(self) -> float:
        """Calculate rows processed per second."""
        duration = self.duration()
        if duration == 0:
            return 0.0
        return self.rows_processed / duration

    @property
    def mb_per_second(self) -> float:
        """Calculate megabytes downloaded per second."""
        duration = self.duration()
        if duration == 0:
            return 0.0
        return (self.bytes_downloaded / 1024 / 1024) / duration

    def __str__(self) -> str:
        return (
            f"FileDownloadResponse(files={self.files_processed}/{self.total_files}, "
            f"rows={self.rows_processed}, "
            f"bytes={self.bytes_downloaded}, "
            f"duration={self.duration():.2f}s, "
            f"failed={len(self.failed_files)})"
        )

    @classmethod
    def extract_from_dict(cls, text_data: str) -> FileDownloadResponse:
        """Create an instance from JSON data.

        Args:
            data (dict): Dict data to create the instance from

        Returns:
            FileDownloadResponse: An instance of FileDownloadResponse
        """
        try:
            files = dict_snake_case({"list": json.loads(text_data)})["list"]
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f"Failed to parse JSON: {text_data}",
                cause=e,
            ) from e

        if not files and not isinstance(files, list):
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f'Expected "files" to be a list, got type: {type(files)}. Value: {files}',
            )

        if len(files) > 0:
            file = files[0]
            if not file.get("url") or not file.get("file"):
                raise ClgxException(
                    error=CommonErrorCodes.API_INVALID_RESPONSE,
                    message=f'Expected list of "files(file,url)" in response, got: {text_data}',
                )
        instance = cls()
        instance.signed_urls = [SignedUrl.from_dict(signed_url) for signed_url in files]
        return instance
