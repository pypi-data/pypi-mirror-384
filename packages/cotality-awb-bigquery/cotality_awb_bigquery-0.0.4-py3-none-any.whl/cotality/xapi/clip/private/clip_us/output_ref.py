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
"""CLIP Output Reference Service - Manage clip output references."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional, Tuple

from dataclasses_json import DataClassJsonMixin

from .....core.interfaces.database import DatabaseClient
from .....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from .....core.interfaces.table import Table
from ...typing import (
    COTALITY_APP_ROLE,
    INPUT_COLUMNS_GROUP,
    META_COLUMNS_GROUP,
    PRIMARY_KEY_GROUP,
    ClipOutputReferenceColumns,
    ClipSummaryMetrics,
)


class Columns(enum.Enum):
    """Column names for the CLIP output reference table."""

    # Clip input colmns
    REFERENCE_ID = ClipOutputReferenceColumns.REFERENCE_ID.value

    STREET_ADDRESS = "street_address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    FULL_ADDRESS = ClipOutputReferenceColumns.FULL_ADDRESS.value
    APN = "apn"
    FIPS_CODE = "fips_code"
    OWNER_NAME_1 = ClipOutputReferenceColumns.OWNER_NAME_1.value
    OWNER_NAME_2 = ClipOutputReferenceColumns.OWNER_NAME_2.value
    LATITUDE = ClipOutputReferenceColumns.LATITUDE.value
    LONGITUDE = ClipOutputReferenceColumns.LONGITUDE.value
    # Meta columns
    NORMALIZED_FULL_ADDRESS = ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value
    PREVIOUS_HASH = ClipOutputReferenceColumns.PREVIOUS_HASH.value
    CURRENT_HASH = ClipOutputReferenceColumns.CURRENT_HASH.value
    CLIP_STATUS = ClipOutputReferenceColumns.CLIP_STATUS.value
    MESSAGE = ClipOutputReferenceColumns.MESSAGE.value
    MESSAGE_DETAILS = ClipOutputReferenceColumns.MESSAGE_DETAILS.value
    NEXT_RETRY_AT = ClipOutputReferenceColumns.NEXT_RETRY_AT.value
    RETRY_ATTEMPTS = ClipOutputReferenceColumns.RETRY_ATTEMPTS.value

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(init=True, frozen=False)
class ClipOutputReference(DataClassJsonMixin):
    """CLIP Output Reference dataclass model.

    This dataclass represents the structure of CLIP output reference data
    that tracks processing status, retry attempts, and hash values for CLIP operations.
    """

    # === PRIMARY KEY FIELDS ===
    reference_id: str  # Unique reference identifier for the record

    # === REQUIRED FIELDS ===
    current_hash: str  # Current hash value (required)
    clip_status: str  # CLIP processing status (required)
    next_retry_at: int  # Next retry timestamp (required)
    retry_attempts: int  # Number of retry attempts (required)

    # === ADDRESS FIELDS ===
    street_address: Optional[str] = None  # Street address of the property
    city: Optional[str] = None  # City name
    state: Optional[str] = None  # State abbreviation
    zip_code: Optional[str] = None  # ZIP code
    full_address: Optional[str] = None  # Complete formatted address

    # === PROPERTY FIELDS ===
    apn: Optional[str] = None  # Assessor's Parcel Number
    fips_code: Optional[str] = None  # Federal Information Processing Standards code

    # === OWNER FIELDS ===
    owner_name_1: Optional[str] = None  # Primary owner name
    owner_name_2: Optional[str] = None  # Secondary owner name

    # === LOCATION FIELDS ===
    latitude: Optional[float] = None  # Geographic latitude coordinate
    longitude: Optional[float] = None  # Geographic longitude coordinate

    # === NORMALIZED DATA ===
    normalized_full_address: Optional[str] = None  # Normalized full address

    # === HASH FIELDS ===
    previous_hash: Optional[str] = None  # Previous hash value

    # === MESSAGE FIELDS ===
    message: Optional[str] = None  # Status message
    message_details: Optional[str] = None  # Detailed status message


class ClipOutputReferenceTableUS(Table):
    """CLIP Output Reference Table extending the base Table class.

    This class provides a pre-configured Table for CLIP output reference data
    that tracks processing status and retry information. The table name is dynamic
    and provided by the customer.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        """Initialize the ClipOutputReferenceTable.

        Args:
            database_client (DatabaseClient): Database client instance
            database_name (str): Name of the database
            schema_name (str): Name of the schema
            table_name (str): Dynamic table name provided by customer
        """
        super().__init__(
            database_client=database_client,
            dataclass_type=ClipOutputReference,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            columns=_SCHEMA.copy(),  # Copy to prevent external modification
            description="CLIP output reference data table for tracking processing status",
            app_role=COTALITY_APP_ROLE,
        )


# ============ Private Schema Definition ============
_SCHEMA = [
    ColumnDefinition(
        name=Columns.REFERENCE_ID.value,
        data_type=DataTypeEnum.TEXT,
        description="Unique reference identifier for the record",
        nullable=False,
        primary_key=True,
        group=PRIMARY_KEY_GROUP,
    ),
    ColumnDefinition(
        name=Columns.STREET_ADDRESS.value,
        data_type=DataTypeEnum.TEXT,
        description="Street address of the property",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CITY.value,
        data_type=DataTypeEnum.TEXT,
        description="City name",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.STATE.value,
        data_type=DataTypeEnum.TEXT,
        description="State abbreviation",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.ZIP_CODE.value,
        data_type=DataTypeEnum.TEXT,
        description="ZIP code",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.FULL_ADDRESS.value,
        data_type=DataTypeEnum.TEXT,
        description="Complete formatted address",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.APN.value,
        data_type=DataTypeEnum.TEXT,
        description="Assessor's Parcel Number",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.FIPS_CODE.value,
        data_type=DataTypeEnum.TEXT,
        description="Federal Information Processing Standards code",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.OWNER_NAME_1.value,
        data_type=DataTypeEnum.TEXT,
        description="Primary owner name",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.OWNER_NAME_2.value,
        data_type=DataTypeEnum.TEXT,
        description="Secondary owner name",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.LATITUDE.value,
        data_type=DataTypeEnum.FLOAT64,
        description="Geographic latitude coordinate",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.LONGITUDE.value,
        data_type=DataTypeEnum.FLOAT64,
        description="Geographic longitude coordinate",
        nullable=True,
        group=INPUT_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.NORMALIZED_FULL_ADDRESS.value,
        data_type=DataTypeEnum.TEXT,
        description="Normalized full address",
        nullable=True,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.PREVIOUS_HASH.value,
        data_type=DataTypeEnum.TEXT,
        description="Previous hash value",
        nullable=True,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CURRENT_HASH.value,
        data_type=DataTypeEnum.TEXT,
        description="Current hash value",
        nullable=False,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STATUS.value,
        data_type=DataTypeEnum.TEXT,
        description="CLIP processing status",
        nullable=False,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.MESSAGE.value,
        data_type=DataTypeEnum.TEXT,
        description="Status message",
        nullable=True,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.MESSAGE_DETAILS.value,
        data_type=DataTypeEnum.TEXT,
        description="Detailed status message",
        nullable=True,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.NEXT_RETRY_AT.value,
        data_type=DataTypeEnum.INT64,
        description="Next retry timestamp",
        nullable=False,
        group=META_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.RETRY_ATTEMPTS.value,
        data_type=DataTypeEnum.INT64,
        description="Number of retry attempts",
        nullable=False,
        group=META_COLUMNS_GROUP,
    ),
]

# ============ Usage Examples ============
#
# # Create database client and table instance with dynamic table name
# db_client = SnowflakeClient(config)
# ref_table = ClipOutputReferenceTable(
#     database_client=db_client,
#     database_name="customer_db",
#     schema_name="clip_reference",
#     table_name="customer_clip_refs_2024"  # Dynamic name from customer
# )
#
# # Create the table in database
# ref_table.create()
#
# # Insert a new reference record
# clip_ref = ClipOutputReference(
#     reference_id="REF_001",
#     street_address="123 Main St",
#     city="Los Angeles",
#     state="CA",
#     zip_code="90001",
#     full_address="123 Main St, Los Angeles, CA 90001",
#     apn="1234-567-890",
#     fips_code="06037",
#     owner_name_1="John Doe",
#     owner_name_2="Jane Doe",
#     latitude=34.0522,
#     longitude=-118.2437,
#     normalized_full_address="123 MAIN ST LOS ANGELES CA 90001",
#     previous_hash=None,
#     current_hash="abc123def456",
#     clip_status="PENDING",
#     message=None,
#     message_details=None,
#     next_retry_at=1738368000,  # Unix timestamp
#     retry_attempts=0
# )
# ref_table.insert(clip_ref)
#
# # Get a reference record by primary key
# record = ref_table.get("REF_001")
# print(f"CLIP Status: {record.clip_status}")
# print(f"Retry Attempts: {record.retry_attempts}")
#
# # Select records with filtering
# pending_records = ref_table.select("clip_status = ?", ["PENDING"])
# failed_records = ref_table.select("retry_attempts > ?", [3])
#
# # Update a record with new status
# record.clip_status = "COMPLETED"
# record.message = "Successfully processed"
# ref_table.update(record)
#
# # Batch insert with duplicate checking
# new_records = [
#     ClipOutputReference(reference_id="REF_002", current_hash="def789ghi012", clip_status="PENDING", next_retry_at=1738368000, retry_attempts=0),
#     ClipOutputReference(reference_id="REF_003", current_hash="jkl345mno678", clip_status="PENDING", next_retry_at=1738368000, retry_attempts=0),
# ]
# ref_table.insert(new_records, if_not_exists=True)
#
# # Access column names via enum
# ref_col = ref_table.columns.REFERENCE_ID  # Returns "reference_id"
# status_col = ref_table.columns.CLIP_STATUS  # Returns "clip_status"
# retry_col = ref_table.columns.RETRY_ATTEMPTS  # Returns "retry_attempts"
#
# # Query for records needing retry
# import time
# current_time = int(time.time())
# retry_candidates = ref_table.select(
#     "clip_status = ? AND next_retry_at <= ? AND retry_attempts < ?",
#     ["FAILED", current_time, 5]
# )
#
# # Get column information for dynamic queries
# primary_columns = ref_table.get_column_names(primary_only=True)
# # Returns: ['reference_id']
#
# all_columns = ref_table.get_column_names()
# # Returns: ['reference_id', 'street_address', 'city', ...]
