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
"""CLIP Input Service - Manage customer clip input data."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from .....core.clgxtyping import AddressAliases
from .....core.interfaces.database import DatabaseClient
from .....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from .....core.interfaces.table import Table
from ...typing import COTALITY_APP_ROLE


class Columns(enum.Enum):
    """Column names for the CLIP input table."""

    REFERENCE_ID = "reference_id"
    STREET_ADDRESS = AddressAliases.STREET_ADDRESS.value
    CITY = AddressAliases.CITY.value
    STATE = AddressAliases.STATE.value
    ZIP_CODE = AddressAliases.ZIP_CODE.value
    FULL_ADDRESS = "full_address"
    APN = AddressAliases.APN.value
    FIPS_CODE = AddressAliases.FIPS_CODE.value
    OWNER_NAME_1 = "owner_name_1"
    OWNER_NAME_2 = "owner_name_2"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


REQUIRED_CLIP_COLUMNS = [
    Columns.REFERENCE_ID.value,
    Columns.STREET_ADDRESS.value,
    Columns.CITY.value,
    Columns.STATE.value,
    Columns.ZIP_CODE.value,
    Columns.FULL_ADDRESS.value,
    Columns.APN.value,
    Columns.FIPS_CODE.value,
    Columns.LATITUDE.value,
    Columns.LONGITUDE.value,
]


@dataclass(init=True, frozen=False)
class ClipInput(DataClassJsonMixin):
    """CLIP Input dataclass model.

    This dataclass represents the structure of customer clip input data
    with business-friendly field names that map to database columns.
    """

    # === PRIMARY KEY FIELDS ===
    reference_id: str  # Unique reference identifier for the input record

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


class ClipInputTableUS(Table):
    """CLIP Input Table extending the base Table class.

    This class provides a pre-configured Table for customer clip input data
    with built-in schema and specialized methods. The table name is dynamic
    and provided by the customer.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        """Initialize the ClipInputTable.

        Args:
            database_client (DatabaseClient): Database client instance
            database_name (str): Name of the database
            schema_name (str): Name of the schema
            table_name (str): Dynamic table name provided by customer
        """
        super().__init__(
            database_client=database_client,
            dataclass_type=ClipInput,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            columns=_SCHEMA.copy(),  # Copy to prevent external modification
            description="Customer CLIP input data table",
            app_role=COTALITY_APP_ROLE,
        )

    @property
    def required_clip_columns(self) -> list[str]:
        """Get the list of required CLIP columns.

        Returns:
            List[str]: List of required column names
        """
        return REQUIRED_CLIP_COLUMNS


# ============ Private Schema Definition ============
_SCHEMA = [
    ColumnDefinition(
        name=Columns.REFERENCE_ID.value,
        data_type=DataTypeEnum.TEXT,
        description="Unique reference identifier for the input record",
        nullable=False,
        primary_key=True,
    ),
    ColumnDefinition(
        name=Columns.STREET_ADDRESS.value,
        data_type=DataTypeEnum.TEXT,
        description="Street address of the property",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.CITY.value,
        data_type=DataTypeEnum.TEXT,
        description="City name",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.STATE.value,
        data_type=DataTypeEnum.TEXT,
        description="State abbreviation",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.ZIP_CODE.value,
        data_type=DataTypeEnum.TEXT,
        description="ZIP code",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.FULL_ADDRESS.value,
        data_type=DataTypeEnum.TEXT,
        description="Complete formatted address",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.APN.value,
        data_type=DataTypeEnum.TEXT,
        description="Assessor's Parcel Number",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.FIPS_CODE.value,
        data_type=DataTypeEnum.TEXT,
        description="Federal Information Processing Standards code",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.OWNER_NAME_1.value,
        data_type=DataTypeEnum.TEXT,
        description="Primary owner name",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.OWNER_NAME_2.value,
        data_type=DataTypeEnum.TEXT,
        description="Secondary owner name",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.LATITUDE.value,
        data_type=DataTypeEnum.FLOAT64,
        description="Geographic latitude coordinate",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.LONGITUDE.value,
        data_type=DataTypeEnum.FLOAT64,
        description="Geographic longitude coordinate",
        nullable=True,
    ),
]

# ============ Usage Examples ============
#
# # Create database client and table instance with dynamic table name
# db_client = SnowflakeClient(config)
# input_table = ClipInputTable(
#     database_client=db_client,
#     database_name="customer_db",
#     schema_name="input",
#     table_name="customer_properties_2024"  # Dynamic name from customer
# )
#
# # Create the table in database
# input_table.create()
#
# # Insert a new record
# clip_input = ClipInput(
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
#     longitude=-118.2437
# )
# input_table.insert(clip_input)
#
# # Get a record by primary key
# record = input_table.get("REF_001")
# print(f"Address: {record.full_address}")
#
# # Select records with filtering
# ca_properties = input_table.select("state = ?", ["CA"])
#
# # Update a record
# record.city = "San Francisco"
# input_table.update(record)
#
# # Batch insert with duplicate checking
# new_records = [
#     ClipInput(reference_id="REF_002", street_address="456 Oak Ave", ...),
#     ClipInput(reference_id="REF_003", street_address="789 Pine Rd", ...),
# ]
# input_table.insert(new_records, if_not_exists=True)
#
# # Access column names via enum
# ref_col = input_table.columns.REFERENCE_ID  # Returns "reference_id"
# address_col = input_table.columns.STREET_ADDRESS  # Returns "street_address"
