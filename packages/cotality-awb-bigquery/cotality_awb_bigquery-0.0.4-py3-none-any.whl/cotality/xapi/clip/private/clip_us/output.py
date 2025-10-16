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
"""CLIP Output Service - Manage customer clip output data with CLIP API responses."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from .....core.clgxtyping import AddressAliases
from .....core.interfaces.database import DatabaseClient
from .....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from .....core.interfaces.table import Table
from ...typing import (
    CLIP_COLUMNS_GROUP,
    COTALITY_APP_ROLE,
    INPUT_COLUMNS_GROUP,
    PRIMARY_KEY_GROUP,
    ClipSummaryMetrics,
)
from .typing import CLIP_SUBMIT_API_V2


class Columns(enum.Enum):
    """Column names for the CLIP output table."""

    REFERENCE_ID = AddressAliases.REFERENCE_ID.value
    STREET_ADDRESS = AddressAliases.STREET_ADDRESS.value
    CITY = AddressAliases.CITY.value
    STATE = AddressAliases.STATE.value
    ZIP_CODE = AddressAliases.ZIP_CODE.value
    FULL_ADDRESS = AddressAliases.FULL_ADDRESS.value
    APN = AddressAliases.APN.value
    FIPS_CODE = AddressAliases.FIPS_CODE.value
    OWNER_NAME_1 = AddressAliases.OWNER_NAME_1
    OWNER_NAME_2 = AddressAliases.OWNER_NAME_2
    LATITUDE = AddressAliases.LATITUDE.value
    LONGITUDE = AddressAliases.LONGITUDE.value
    CLIP_ID = "clip_id"
    CLIP_CLIP_STATUS_CODE = "clip_status_code"
    CLIP_APN_SEQUENCE_NUMBER = "clip_apn_sequence_number"
    CLIP_UNIVERSAL_PARCEL_ID = "clip_universal_parcel_id"
    CLIP_COUNTY_CODE = "clip_county_code"
    CLIP_LATITUDE = "clip_latitude"
    CLIP_LONGITUDE = "clip_longitude"
    CLIP_APN_UNFORMATTED = "clip_apn_unformatted"
    CLIP_APN_FORMATTED = "clip_apn_formatted"
    CLIP_PREVIOUS_APN_UNFORMATTED = "clip_previous_apn_unformatted"
    CLIP_FULL_ADDRESS = "clip_full_address"
    CLIP_ADDRESS_LINE = "clip_address_line"
    CLIP_HOUSE_NUMBER = "clip_house_number"
    CLIP_UNIT_NUMBER = "clip_unit_number"
    CLIP_UNIT_TYPE = "clip_unit_type"
    CLIP_STREET_NAME = "clip_street_name"
    CLIP_STREET_NAME_FULL = "clip_street_name_full"
    CLIP_STREET_NAME_SUFFIX = "clip_street_name_suffix"
    CLIP_STREET_NAME_PREFIX = "clip_street_name_prefix"
    CLIP_STREET_NAME_PREFIX_DIRECTION = "clip_street_name_prefix_direction"
    CLIP_CITY_LINE = "clip_city_line"
    CLIP_CITY = "clip_city"
    CLIP_STATE = "clip_state"
    CLIP_ZIP_CODE = "clip_zip_code"
    CLIP_COUNTY = "clip_county"
    CLIP_COUNTRY_CODE = "clip_country_code"
    CLIP_ZIP_PLUS4 = "clip_zip_plus4"
    CLIP_MATCH_CODE = "clip_match_code"
    CLIP_PROPERTY_MATCH_SCORE = "clip_property_match_score"
    CLIP_STREET_SIDE = "clip_street_side"
    CLIP_STREET_NAME_BASE = "clip_street_name_base"
    CLIP_STREET_NAME_SUFFIX_DIRECTION = "clip_street_name_suffix_direction"
    CLIP_UNIT_RANGE_HIGH = "clip_unit_range_high"
    CLIP_UNIT_RANGE_LOW = "clip_unit_range_low"
    CLIP_OWNER1_NAME = "clip_owner1_name"
    CLIP_OWNER2_NAME = "clip_owner2_name"
    CLIP_ADDRESS_ID = "clip_address_id"
    CLIP_USPS_RECOMMENDED_CITY = "clip_usps_recommended_city"
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_ID = "clip_address_attributes_address_id"
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_TYPE = "clip_address_attributes_address_type"
    CLIP_ADDRESS_ATTRIBUTES_FULL_ADDRESS = "clip_address_attributes_full_address"
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_LINE = "clip_address_attributes_address_line"
    CLIP_ADDRESS_ATTRIBUTES_HOUSE_NUMBER = "clip_address_attributes_house_number"
    CLIP_ADDRESS_ATTRIBUTES_UNIT_NUMBER = "clip_address_attributes_unit_number"
    CLIP_ADDRESS_ATTRIBUTES_UNIT_TYPE = "clip_address_attributes_unit_type"
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME = "clip_address_attributes_street_name"
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_SUFFIX = (
        "clip_address_attributes_street_name_suffix"
    )
    CLIP_ADDRESS_ATTRIBUTES_CITY_LINE = "clip_address_attributes_city_line"
    CLIP_ADDRESS_ATTRIBUTES_CITY = "clip_address_attributes_city"
    CLIP_ADDRESS_ATTRIBUTES_STATE = "clip_address_attributes_state"
    CLIP_ADDRESS_ATTRIBUTES_ZIP_CODE = "clip_address_attributes_zip_code"
    CLIP_ADDRESS_ATTRIBUTES_COUNTRY_CODE = "clip_address_attributes_country_code"
    CLIP_ADDRESS_ATTRIBUTES_LATITUDE = "clip_address_attributes_latitude"
    CLIP_ADDRESS_ATTRIBUTES_LONGITUDE = "clip_address_attributes_longitude"
    CLIP_ADDRESS_ATTRIBUTES_ZIP_PLUS4 = "clip_address_attributes_zip_plus4"
    CLIP_ADDRESS_ATTRIBUTES_STREET_SIDE = "clip_address_attributes_street_side"
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_PREFIX = (
        "clip_address_attributes_street_name_prefix"
    )
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_PREFIX_DIRECTION = (
        "clip_address_attributes_street_name_prefix_direction"
    )
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_BASE = (
        "clip_address_attributes_street_name_base"
    )
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_SUFFIX_DIRECTION = (
        "clip_address_attributes_street_name_suffix_direction"
    )
    CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_FULL = (
        "clip_address_attributes_street_name_full"
    )
    CLIP_ADDRESS_ATTRIBUTES_UNIT_RANGE_HIGH = "clip_address_attributes_unit_range_high"
    CLIP_ADDRESS_ATTRIBUTES_UNIT_RANGE_LOW = "clip_address_attributes_unit_range_low"
    CLIP_ADDRESS_ATTRIBUTES_GEOCODE_DATA_SET = (
        "clip_address_attributes_geocode_data_set"
    )
    CLIP_ADDRESS_ATTRIBUTES_GEOCODE_VENDOR = "clip_address_attributes_geocode_vendor"
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_CODE = (
        "clip_address_attributes_address_match_code"
    )
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_DESCRIPTION = (
        "clip_address_attributes_address_match_description"
    )
    CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_RECORD = (
        "clip_address_attributes_address_match_record"
    )
    CLIP_ADDRESS_ATTRIBUTES_USPS_RECOMMENDED_CITY = (
        "clip_address_attributes_usps_recommended_city"
    )
    CLIP_ADDRESS_ATTRIBUTES_ADMIN1 = "clip_address_attributes_admin1"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN2 = "clip_address_attributes_admin2"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN3 = "clip_address_attributes_admin3"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN4 = "clip_address_attributes_admin4"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN5 = "clip_address_attributes_admin5"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN6 = "clip_address_attributes_admin6"
    CLIP_ADDRESS_ATTRIBUTES_ADMIN7 = "clip_address_attributes_admin7"
    CLIP_RESPONSE_STATUS = "clip_response_status"
    CLIP_RESULT_CODE = "clip_result_code"
    CLIP_PAGE_SIZE = "clip_page_size"
    CLIP_TOTAL_RECORDS = "clip_total_records"
    CLIP_TOTAL_PAGES = "clip_total_pages"
    CLIP_PAGE_NUMBER = "clip_page_number"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(init=True, frozen=False)
class ClipOutput(DataClassJsonMixin):
    """CLIP Output dataclass model.

    This dataclass represents the structure of CLIP output data
    combining customer input with CLIP API responses with business-friendly field names
    that map to database columns.
    """

    # === PRIMARY KEY FIELDS ===
    reference_id: str  # Unique reference identifier for the input record

    # === CUSTOMER INPUT ADDRESS FIELDS ===
    street_address: Optional[str] = None  # Street address of the property
    city: Optional[str] = None  # City name
    state: Optional[str] = None  # State abbreviation
    zip_code: Optional[str] = None  # ZIP code
    full_address: Optional[str] = None  # Complete formatted address

    # === CUSTOMER INPUT PROPERTY FIELDS ===
    apn: Optional[str] = None  # Assessor's Parcel Number
    fips_code: Optional[str] = None  # Federal Information Processing Standards code

    # === CUSTOMER INPUT OWNER FIELDS ===
    owner_name_1: Optional[str] = None  # Primary owner name
    owner_name_2: Optional[str] = None  # Secondary owner name

    # === CUSTOMER INPUT LOCATION FIELDS ===
    latitude: Optional[float] = None  # Geographic latitude coordinate
    longitude: Optional[float] = None  # Geographic longitude coordinate

    # === CLIP API RESPONSE FIELDS ===
    clip_id: Optional[str] = None  # CLIP identifier
    clip_clip_status: Optional[str] = None  # CLIP processing status
    clip_apn_sequence_number: Optional[int] = None  # APN sequence number
    clip_universal_parcel_id: Optional[str] = None  # Universal parcel identifier
    clip_county_code: Optional[str] = None  # County code
    clip_latitude: Optional[float] = None  # CLIP latitude coordinate
    clip_longitude: Optional[float] = None  # CLIP longitude coordinate
    clip_apn_unformatted: Optional[str] = None  # Unformatted APN
    clip_apn_formatted: Optional[str] = None  # Formatted APN
    clip_previous_apn_unformatted: Optional[str] = None  # Previous unformatted APN
    clip_full_address: Optional[str] = None  # CLIP full address
    clip_address_line: Optional[str] = None  # CLIP address line
    clip_house_number: Optional[str] = None  # House number
    clip_unit_number: Optional[str] = None  # Unit number
    clip_unit_type: Optional[str] = None  # Unit type
    clip_street_name: Optional[str] = None  # Street name
    clip_street_name_full: Optional[str] = None  # Full street name
    clip_street_name_suffix: Optional[str] = None  # Street name suffix
    clip_street_name_prefix: Optional[str] = None  # Street name prefix
    clip_street_name_prefix_direction: Optional[str] = (
        None  # Street name prefix direction
    )
    clip_city_line: Optional[str] = None  # City line
    clip_city: Optional[str] = None  # CLIP city
    clip_state: Optional[str] = None  # CLIP state
    clip_zip_code: Optional[str] = None  # CLIP ZIP code
    clip_county: Optional[str] = None  # CLIP county
    clip_country_code: Optional[str] = None  # CLIP country code
    clip_zip_plus4: Optional[str] = None  # CLIP ZIP+4
    clip_match_code: Optional[str] = None  # Match code
    clip_property_match_score: Optional[float] = None  # Property match score
    clip_street_side: Optional[str] = None  # Street side
    clip_street_name_base: Optional[str] = None  # Street name base
    clip_street_name_suffix_direction: Optional[str] = (
        None  # Street name suffix direction
    )
    clip_unit_range_high: Optional[str] = None  # Unit range high
    clip_unit_range_low: Optional[str] = None  # Unit range low
    clip_owner1_name: Optional[str] = None  # CLIP owner 1 name
    clip_owner2_name: Optional[str] = None  # CLIP owner 2 name
    clip_address_id: Optional[str] = None  # Address ID
    clip_usps_recommended_city: Optional[str] = None  # USPS recommended city

    # === CLIP ADDRESS ATTRIBUTES ===
    clip_address_attributes_address_id: Optional[str] = (
        None  # Address attributes address ID
    )
    clip_address_attributes_address_type: Optional[str] = (
        None  # Address attributes address type
    )
    clip_address_attributes_full_address: Optional[str] = (
        None  # Address attributes full address
    )
    clip_address_attributes_address_line: Optional[str] = (
        None  # Address attributes address line
    )
    clip_address_attributes_house_number: Optional[str] = (
        None  # Address attributes house number
    )
    clip_address_attributes_unit_number: Optional[str] = (
        None  # Address attributes unit number
    )
    clip_address_attributes_unit_type: Optional[str] = (
        None  # Address attributes unit type
    )
    clip_address_attributes_street_name: Optional[str] = (
        None  # Address attributes street name
    )
    clip_address_attributes_street_name_suffix: Optional[str] = (
        None  # Address attributes street name suffix
    )
    clip_address_attributes_city_line: Optional[str] = (
        None  # Address attributes city line
    )
    clip_address_attributes_city: Optional[str] = None  # Address attributes city
    clip_address_attributes_state: Optional[str] = None  # Address attributes state
    clip_address_attributes_zip_code: Optional[str] = (
        None  # Address attributes ZIP code
    )
    clip_address_attributes_country_code: Optional[str] = (
        None  # Address attributes country code
    )
    clip_address_attributes_latitude: Optional[float] = (
        None  # Address attributes latitude
    )
    clip_address_attributes_longitude: Optional[float] = (
        None  # Address attributes longitude
    )
    clip_address_attributes_zip_plus4: Optional[str] = None  # Address attributes ZIP+4
    clip_address_attributes_street_side: Optional[str] = (
        None  # Address attributes street side
    )
    clip_address_attributes_street_name_prefix: Optional[str] = (
        None  # Address attributes street name prefix
    )
    clip_address_attributes_street_name_prefix_direction: Optional[str] = (
        None  # Address attributes street name prefix direction
    )
    clip_address_attributes_street_name_base: Optional[str] = (
        None  # Address attributes street name base
    )
    clip_address_attributes_street_name_suffix_direction: Optional[str] = (
        None  # Address attributes street name suffix direction
    )
    clip_address_attributes_street_name_full: Optional[str] = (
        None  # Address attributes street name full
    )
    clip_address_attributes_unit_range_high: Optional[str] = (
        None  # Address attributes unit range high
    )
    clip_address_attributes_unit_range_low: Optional[str] = (
        None  # Address attributes unit range low
    )
    clip_address_attributes_geocode_data_set: Optional[str] = (
        None  # Address attributes geocode data set
    )
    clip_address_attributes_geocode_vendor: Optional[str] = (
        None  # Address attributes geocode vendor
    )
    clip_address_attributes_address_match_code: Optional[str] = (
        None  # Address attributes address match code
    )
    clip_address_attributes_address_match_description: Optional[str] = (
        None  # Address attributes address match description
    )
    clip_address_attributes_address_match_record: Optional[str] = (
        None  # Address attributes address match record
    )
    clip_address_attributes_usps_recommended_city: Optional[str] = (
        None  # Address attributes USPS recommended city
    )
    clip_address_attributes_admin1: Optional[str] = (
        None  # Address attributes admin level 1
    )
    clip_address_attributes_admin2: Optional[str] = (
        None  # Address attributes admin level 2
    )
    clip_address_attributes_admin3: Optional[str] = (
        None  # Address attributes admin level 3
    )
    clip_address_attributes_admin4: Optional[str] = (
        None  # Address attributes admin level 4
    )
    clip_address_attributes_admin5: Optional[str] = (
        None  # Address attributes admin level 5
    )
    clip_address_attributes_admin6: Optional[str] = (
        None  # Address attributes admin level 6
    )
    clip_address_attributes_admin7: Optional[str] = (
        None  # Address attributes admin level 7
    )

    # === CLIP PAGINATION AND STATUS ===
    clip_status: Optional[int] = None  # CLIP status code
    clip_result_code: Optional[str] = None  # CLIP result code
    clip_page_size: Optional[int] = None  # Page size
    clip_total_records: Optional[int] = None  # Total records
    clip_total_pages: Optional[int] = None  # Total pages
    clip_page_number: Optional[int] = None  # Current page number


CLIP_METRICS_KEYS_TO_CLIP_OUTPUT_COLUMNS = {
    "property_match_score": Columns.CLIP_PROPERTY_MATCH_SCORE.value,
    "result_code": Columns.CLIP_RESULT_CODE.value,
    "match_code": Columns.CLIP_MATCH_CODE.value,
    "address_type": Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_TYPE.value,
    "address_match_code": Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_CODE.value,
}


class ClipOutputTable(Table):
    """CLIP Output Table extending the base Table class.

    This class provides a pre-configured Table for CLIP output data
    combining customer input with CLIP API responses. The table name is dynamic
    and provided by the customer.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        database_name: str,
        schema_name: str,
        table_name: str,
    ):
        """Initialize the ClipOutputTable.

        Args:
            database_client (DatabaseClient): Database client instance
            database_name (str): Name of the database
            schema_name (str): Name of the schema
            table_name (str): Dynamic table name provided by customer
        """
        super().__init__(
            database_client=database_client,
            dataclass_type=ClipOutput,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            columns=_SCHEMA.copy(),  # Copy to prevent external modification
            description="CLIP output data table combining customer input with CLIP API responses",
            app_role=COTALITY_APP_ROLE,
        )

    def aggregate_clip_metric(self, table_name: str) -> ClipSummaryMetrics:
        """Aggregate property match score from the Clip output table.
        Args:
            table_name (str): Name of the table
        Returns:
            ClipSummaryMetrics: Aggregated property match score
        """
        table_name = self.get_table_name(table_name)
        clip_summary_metric = ClipSummaryMetrics()
        for key in clip_summary_metric.to_dict().keys():
            clip_output_column_name = CLIP_METRICS_KEYS_TO_CLIP_OUTPUT_COLUMNS[key]
            sql = f"""
                SELECT {clip_output_column_name} AS score, COUNT(*) AS count
                FROM {table_name}
                GROUP BY {clip_output_column_name}
                ORDER BY score DESC
            """
            aggr_result = self._database_client.query_to_dict(sql)
            clip_summary_metric.__dict__[key] = {
                result.get("score"): result.get("count")
                for result in aggr_result
                if result.get("score") is not None
            }

        return clip_summary_metric


# ============ Private Schema Definition ============
_SCHEMA = [
    # Customer input fields
    ColumnDefinition(
        name=Columns.REFERENCE_ID.value,
        data_type=DataTypeEnum.TEXT,
        description="Unique reference identifier for the input record",
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
    # CLIP API response fields
    ColumnDefinition(
        name=Columns.CLIP_ID.value,
        alias="clip_clip",
        data_type=DataTypeEnum.TEXT,
        description="CLIP identifier",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_CLIP_STATUS_CODE.value,
        alias="clip_clipStatus",
        data_type=DataTypeEnum.TEXT,
        description="CLIP processing status",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_APN_SEQUENCE_NUMBER.value,
        alias="clip_apnSequenceNumber",
        data_type=DataTypeEnum.INT64,
        description="APN sequence number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_UNIVERSAL_PARCEL_ID.value,
        alias="clip_universalParcelId",
        data_type=DataTypeEnum.INT64,
        description="Universal parcel identifier",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_COUNTY_CODE.value,
        alias="clip_countyCode",
        data_type=DataTypeEnum.TEXT,
        description="County code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_LATITUDE.value,
        alias="clip_latitude",
        data_type=DataTypeEnum.FLOAT64,
        description="CLIP latitude coordinate",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_LONGITUDE.value,
        alias="clip_longitude",
        data_type=DataTypeEnum.FLOAT64,
        description="CLIP longitude coordinate",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_APN_UNFORMATTED.value,
        alias="clip_apnUnformatted",
        data_type=DataTypeEnum.TEXT,
        description="Unformatted APN",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_APN_FORMATTED.value,
        alias="clip_apnFormatted",
        data_type=DataTypeEnum.TEXT,
        description="Formatted APN",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_PREVIOUS_APN_UNFORMATTED.value,
        alias="clip_previousApnUnformatted",
        data_type=DataTypeEnum.TEXT,
        description="Previous unformatted APN",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_FULL_ADDRESS.value,
        alias="clip_fullAddress",
        data_type=DataTypeEnum.TEXT,
        description="CLIP full address",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_LINE.value,
        alias="clip_addressLine",
        data_type=DataTypeEnum.TEXT,
        description="CLIP address line",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_HOUSE_NUMBER.value,
        alias="clip_houseNumber",
        data_type=DataTypeEnum.TEXT,
        description="House number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_UNIT_NUMBER.value,
        alias="clip_unitNumber",
        data_type=DataTypeEnum.TEXT,
        description="Unit number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_UNIT_TYPE.value,
        alias="clip_unitType",
        data_type=DataTypeEnum.TEXT,
        description="Unit type",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME.value,
        alias="clip_streetName",
        data_type=DataTypeEnum.TEXT,
        description="Street name",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_FULL.value,
        alias="clip_streetNameFull",
        data_type=DataTypeEnum.TEXT,
        description="Full street name",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_SUFFIX.value,
        alias="clip_streetNameSuffix",
        data_type=DataTypeEnum.TEXT,
        description="Street name suffix",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_PREFIX.value,
        alias="clip_streetNamePrefix",
        data_type=DataTypeEnum.TEXT,
        description="Street name prefix",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_PREFIX_DIRECTION.value,
        alias="clip_streetNamePrefixDirection",
        data_type=DataTypeEnum.TEXT,
        description="Street name prefix direction",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_CITY_LINE.value,
        alias="clip_cityLine",
        data_type=DataTypeEnum.TEXT,
        description="City line",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_CITY.value,
        alias="clip_city",
        data_type=DataTypeEnum.TEXT,
        description="CLIP city",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STATE.value,
        alias="clip_state",
        data_type=DataTypeEnum.TEXT,
        description="CLIP state",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ZIP_CODE.value,
        alias="clip_zipCode",
        data_type=DataTypeEnum.TEXT,
        description="CLIP ZIP code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_COUNTY.value,
        alias="clip_county",
        data_type=DataTypeEnum.TEXT,
        description="CLIP county",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_COUNTRY_CODE.value,
        alias="clip_countryCode",
        data_type=DataTypeEnum.TEXT,
        description="CLIP country code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ZIP_PLUS4.value,
        alias="clip_zipPlus4",
        data_type=DataTypeEnum.TEXT,
        description="CLIP ZIP+4",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_MATCH_CODE.value,
        alias="clip_matchCode",
        data_type=DataTypeEnum.TEXT,
        description="Match code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_PROPERTY_MATCH_SCORE.value,
        alias="clip_propertyMatchScore",
        data_type=DataTypeEnum.INT64,
        description="Property match score",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_SIDE.value,
        alias="clip_streetSide",
        data_type=DataTypeEnum.TEXT,
        description="Street side",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_BASE.value,
        alias="clip_streetNameBase",
        data_type=DataTypeEnum.TEXT,
        description="Street name base",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_STREET_NAME_SUFFIX_DIRECTION.value,
        alias="clip_streetNameSuffixDirection",
        data_type=DataTypeEnum.TEXT,
        description="Street name suffix direction",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_UNIT_RANGE_HIGH.value,
        alias="clip_unitRangeHigh",
        data_type=DataTypeEnum.TEXT,
        description="Unit range high",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_UNIT_RANGE_LOW.value,
        alias="clip_unitRangeLow",
        data_type=DataTypeEnum.TEXT,
        description="Unit range low",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_OWNER1_NAME.value,
        alias="clip_owner1Name",
        data_type=DataTypeEnum.TEXT,
        description="CLIP owner 1 name",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_OWNER2_NAME.value,
        alias="clip_owner2Name",
        data_type=DataTypeEnum.TEXT,
        description="CLIP owner 2 name",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ID.value,
        alias="clip_addressId",
        data_type=DataTypeEnum.INT64,
        description="Address ID",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_USPS_RECOMMENDED_CITY.value,
        alias="clip_uspsRecommendedCity",
        data_type=DataTypeEnum.TEXT,
        description="USPS recommended city",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    # CLIP Address Attributes
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_ID.value,
        alias="clip_addressAttributes_addressId",
        data_type=DataTypeEnum.INT64,
        description="Address attributes address ID",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_TYPE.value,
        alias="clip_addressAttributes_addressType",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes address type",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_FULL_ADDRESS.value,
        alias="clip_addressAttributes_fullAddress",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes full address",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_LINE.value,
        alias="clip_addressAttributes_addressLine",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes address line",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_HOUSE_NUMBER.value,
        alias="clip_addressAttributes_houseNumber",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes house number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_UNIT_NUMBER.value,
        alias="clip_addressAttributes_unitNumber",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes unit number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_UNIT_TYPE.value,
        alias="clip_addressAttributes_unitType",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes unit type",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME.value,
        alias="clip_addressAttributes_streetName",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_SUFFIX.value,
        alias="clip_addressAttributes_streetNameSuffix",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name suffix",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_CITY_LINE.value,
        alias="clip_addressAttributes_cityLine",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes city line",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_CITY.value,
        alias="clip_addressAttributes_city",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes city",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STATE.value,
        alias="clip_addressAttributes_state",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes state",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ZIP_CODE.value,
        alias="clip_addressAttributes_zipCode",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes ZIP code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_COUNTRY_CODE.value,
        alias="clip_addressAttributes_countryCode",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes country code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_LATITUDE.value,
        alias="clip_addressAttributes_latitude",
        data_type=DataTypeEnum.FLOAT64,
        description="Address attributes latitude",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_LONGITUDE.value,
        alias="clip_addressAttributes_longitude",
        data_type=DataTypeEnum.FLOAT64,
        description="Address attributes longitude",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ZIP_PLUS4.value,
        alias="clip_addressAttributes_zipPlus4",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes ZIP+4",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_SIDE.value,
        alias="clip_addressAttributes_streetSide",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street side",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_PREFIX.value,
        alias="clip_addressAttributes_streetNamePrefix",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name prefix",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_PREFIX_DIRECTION.value,
        alias="clip_addressAttributes_streetNamePrefixDirection",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name prefix direction",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_BASE.value,
        alias="clip_addressAttributes_streetNameBase",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name base",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_SUFFIX_DIRECTION.value,
        alias="clip_addressAttributes_streetNameSuffixDirection",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name suffix direction",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_STREET_NAME_FULL.value,
        alias="clip_addressAttributes_streetNameFull",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes street name full",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_UNIT_RANGE_HIGH.value,
        alias="clip_addressAttributes_unitRangeHigh",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes unit range high",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_UNIT_RANGE_LOW.value,
        alias="clip_addressAttributes_unitRangeLow",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes unit range low",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_GEOCODE_DATA_SET.value,
        alias="clip_addressAttributes_geocodeDataSet",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes geocode data set",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_GEOCODE_VENDOR.value,
        alias="clip_addressAttributes_geocodeVendor",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes geocode vendor",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_CODE.value,
        alias="clip_addressAttributes_addressMatchCode",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes address match code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_DESCRIPTION.value,
        alias="clip_addressAttributes_addressMatchDescription",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes address match description",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADDRESS_MATCH_RECORD.value,
        alias="clip_addressAttributes_addressMatchRecord",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes address match record",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_USPS_RECOMMENDED_CITY.value,
        alias="clip_addressAttributes_uspsRecommendedCity",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes USPS recommended city",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN1.value,
        alias="clip_addressAttributes_admin1",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 1",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN2.value,
        alias="clip_addressAttributes_admin2",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 2",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN3.value,
        alias="clip_addressAttributes_admin3",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 3",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN4.value,
        alias="clip_addressAttributes_admin4",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 4",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN5.value,
        alias="clip_addressAttributes_admin5",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 5",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN6.value,
        alias="clip_addressAttributes_admin6",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 6",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_ADDRESS_ATTRIBUTES_ADMIN7.value,
        alias="clip_addressAttributes_admin7",
        data_type=DataTypeEnum.TEXT,
        description="Address attributes admin level 7",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    # Final status and pagination columns
    ColumnDefinition(
        name=Columns.CLIP_RESPONSE_STATUS.value,
        alias="clip_status",
        data_type=DataTypeEnum.INT64,
        description="CLIP HTTP response status code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_RESULT_CODE.value,
        alias="clip_resultCode",
        data_type=DataTypeEnum.TEXT,
        description="CLIP result code",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_PAGE_SIZE.value,
        alias="clip_pageSize",
        data_type=DataTypeEnum.INT64,
        description="Page size",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_TOTAL_RECORDS.value,
        alias="clip_totalRecords",
        data_type=DataTypeEnum.INT64,
        description="Total records",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_TOTAL_PAGES.value,
        alias="clip_totalPages",
        data_type=DataTypeEnum.INT64,
        description="Total pages",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
    ColumnDefinition(
        name=Columns.CLIP_PAGE_NUMBER.value,
        alias="clip_pageNumber",
        data_type=DataTypeEnum.INT64,
        description="Current page number",
        nullable=True,
        group=CLIP_COLUMNS_GROUP,
    ),
]

# ============ Usage Examples ============
#
# # Create database client and table instance with dynamic table name
# db_client = SnowflakeClient(config)
# output_table = ClipOutputTable(
#     database_client=db_client,
#     database_name="customer_db",
#     schema_name="clip_output",
#     table_name="customer_properties_with_clip_2024"  # Dynamic name from customer
# )
#
# # Create the table in database
# output_table.create()
#
# # Insert a new record combining customer input with CLIP response
# clip_output = ClipOutput(
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
#     # CLIP API response fields
#     clip_id="CLIP_12345",
#     clip_clip_status="MATCHED",
#     clip_full_address="123 MAIN ST LOS ANGELES CA 90001",
#     clip_city="LOS ANGELES",
#     clip_state="CA",
#     clip_zip_code="90001",
#     clip_latitude=34.0522,
#     clip_longitude=-118.2437,
#     clip_match_code="A1",
#     clip_property_match_score=95.5,
#     clip_status=200,
#     clip_result_code="SUCCESS"
# )
# output_table.insert(clip_output)
#
# # Get a record by primary key
# record = output_table.get("REF_001")
# print(f"CLIP Address: {record.clip_full_address}")
# print(f"Match Score: {record.clip_property_match_score}")
#
# # Select records with filtering
# matched_records = output_table.select("clip_clip_status = ?", ["MATCHED"])
#
# # Update a record with additional CLIP data
# record.clip_owner1_name = "JOHN DOE"
# record.clip_address_attributes_city = "LOS ANGELES"
# output_table.update(record)
#
# # Batch insert with duplicate checking
# new_records = [
#     ClipOutput(reference_id="REF_002", clip_id="CLIP_67890", ...),
#     ClipOutput(reference_id="REF_003", clip_id="CLIP_11111", ...),
# ]
# output_table.insert(new_records, if_not_exists=True)
#
# # Access column names via enum
# ref_col = output_table.columns.REFERENCE_ID  # Returns "reference_id"
# clip_status_col = output_table.columns.CLIP_CLIP_STATUS  # Returns "clip_clip_status"
# match_score_col = output_table.columns.CLIP_PROPERTY_MATCH_SCORE  # Returns "clip_property_match_score"
#
# # Query with complex filters
# high_confidence_matches = output_table.select(
#     "clip_property_match_score > ? AND clip_clip_status = ?",
#     [90.0, "MATCHED"]
# )
#
# # Get column information for dynamic queries
# primary_columns = output_table.get_column_names(primary_only=True)
# # Returns: ['reference_id']
#
# all_columns = output_table.get_column_names()
# # Returns: ['reference_id', 'street_address', 'city', ...]
