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
"""Clip Typing."""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin
from pandas import DataFrame as PandaDataFrame

from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from ...core.utils.misc import datetime_to_int

APP_ID = "clip"

COTALITY_APP_ROLE = "COTALITY_APP_ROLE"
CLIP_STEP_LOG_PREFIX = ">>> Step"

# Column groups
PRIMARY_KEY_GROUP = "primary_key"
CLIP_COLUMNS_GROUP = "clip"
INPUT_COLUMNS_GROUP = "input"
META_COLUMNS_GROUP = "meta"

# DMZ Storages
STORAGE_ID = "clip"
STORAGE_INPUT_SUFFIX = "input"
STORAGE_OUTPUT_SUFFIX = "output"


class ClipOutputReferenceColumns(enum.Enum):
    """Column names for the CLIP output table."""

    REFERENCE_ID = "reference_id"
    FULL_ADDRESS = "full_address"
    OWNER_NAME_1 = "owner_name_1"
    OWNER_NAME_2 = "owner_name_2"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    NORMALIZED_FULL_ADDRESS = "normalized_full_address"
    PREVIOUS_HASH = "previous_hash"
    CURRENT_HASH = "current_hash"
    CLIP_STATUS = "clip_status"
    MESSAGE = "message"
    MESSAGE_DETAILS = "message_details"
    NEXT_RETRY_AT = "next_retry_at"
    RETRY_ATTEMPTS = "retry_attempts"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


# ========== Clip Lookup Config ==========
class ClipLookupAction(str, enum.Enum):
    """ClipLookupAction."""

    INITIALIZE = 1
    VALIDATE_SCHEMA = 2
    PREPARRE_INPUT_DATA = 3
    VALIDATE_INPUT_DATA = 4
    UPLOAD_INPUT_DATA = 5
    SUBMIT_JOB = 6
    POLL_JOB = 7
    DOWNLOAD_RESULTS = 8
    SAVE_RESULTS = 9
    CLEANUP = 10

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class RunStatus(str, enum.Enum):
    """ClipLookupFailedReason."""

    # Run status
    UNKNOWN = "unknown"
    RUNNING = "running"
    REJECTED = "rejected"
    # Job status
    SUCCEEDED = "succeeded"
    DUPLICATED_PK = "duplicated_pk"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    FAILED = "failed"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class PropertyClipStatus(str, enum.Enum):
    """PropertyClipStatus."""

    CLIPPED = "clipped"
    NOT_CLIPPED = "not_clipped"
    INVALID = "invalid"
    NEW = "new"
    UPDATED = "updated"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(init=True)
class InputMetrics(DataClassJsonMixin):
    """Input Metrcs."""

    # Total counts
    total_input_counts: int = 0  # Total number of input records

    invalid_counts: int = 0
    invalid_percentage: float = 0.0
    clip_counts: int = 0
    non_clip_counts: int = 0

    def get_total_records_sent_to_clip(self) -> int:
        """Get total records sent to Clip.

        Returns:
            int: Total records sent to Clip
        """
        return self.clip_counts + self.non_clip_counts


@dataclass(init=True)
class ClipSummaryMetrics(DataClassJsonMixin):
    """Clip Summary Metrcs."""

    # Total counts
    property_match_score: dict = field(default_factory=dict)
    result_code: dict = field(default_factory=dict)
    match_code: dict = field(default_factory=dict)
    address_type: dict = field(default_factory=dict)
    address_match_code: dict = field(default_factory=dict)


@dataclass(init=True)
class ClipMetrics(DataClassJsonMixin):
    """Clip  Metrcs."""

    input_metrics: InputMetrics = field(default_factory=InputMetrics)
    clip_summary_metric: ClipSummaryMetrics = field(default_factory=ClipSummaryMetrics)


@dataclass(init=True)
class ClipLookupStatus(DataClassJsonMixin):
    """JobStatus"""

    # Job
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: RunStatus = RunStatus.UNKNOWN
    started_at: int = field(default_factory=datetime_to_int)
    updated_at: int = field(default_factory=datetime_to_int)
    completed_at: int = 0
    elapsed_time_in_seconds: int = 0
    step = ClipLookupAction.INITIALIZE
    exception: ClgxException | None = None
    exception_df: PandaDataFrame | None = None
    # Counts metrics
    input_metrics: InputMetrics = field(default_factory=InputMetrics)
    input_counts: int = 0  # Total number of input records to be sent to Clip API
    batch_input_counts: int = 0
    batch_output_counts: int = 0


# Dataframe column names

# List of input table summary dataframe
INPUT_TABLE_NAME = "input_table_name"
TOTAL_RECORDS = "total_records"
CLIP_OUTPUT_TABLE = "clip_output_table"
TOTAL_CLIP_RECORDS = "total_clip_records"
LAST_CLIP_RUN_DATE = "last_clip_run_date"
LAST_CLIP_RUN_RECORDS = "last_clip_run_records"
LAST_CLIP_RUN_STATUS = "last_clip_run_status"
