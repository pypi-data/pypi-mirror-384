# Copyright 2022 CORELOGIC
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
"""Global types."""
from __future__ import annotations

import enum
import locale
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from . import constants
from .error_codes import CommonErrorCodes
from .exception import ClgxException

# To avoid circular import, need to move SqlConnectionConfig here
# from ..sql.typing import SqlConnectionConfig

# ======================== Misc ==================

UTF8: str = "utf-8"

DEFAULT_HTTP_API_TIMEOUT_IN_SECONDS: int = 10 * 60

CORELOGIC_PATH = ".corelogic"
CORELOGIC_SYSTEM_FOLDER = f"/opt/{CORELOGIC_PATH}"
CORELOGIC_LOCAL_FOLDER = CORELOGIC_PATH
CORELOGIC_HOME_FOLDER = f"{Path.home()}/{CORELOGIC_PATH}"

# Sub-folder under CORELOGIC_FOLDER
LOCAL_STORAGE_ZONE_FOLDER = CORELOGIC_HOME_FOLDER + "/data/file"
LOCAL_DATASET_ZONE_FOLDER = CORELOGIC_HOME_FOLDER + "/data/ds"
LOCAL_LOG_FOLDER = CORELOGIC_HOME_FOLDER + "/logs"
CONFIG_PATH = "config"
LOCAL_CONFIG_FOLDER = CORELOGIC_HOME_FOLDER + "/" + CONFIG_PATH

CONFIG_FOLDERS = [
    CORELOGIC_SYSTEM_FOLDER + "/" + CONFIG_PATH,
    CORELOGIC_HOME_FOLDER + "/" + CONFIG_PATH,
    CORELOGIC_PATH + "/" + CONFIG_PATH,
]

LOCAL_FOLDERS = [
    LOCAL_STORAGE_ZONE_FOLDER,
    LOCAL_DATASET_ZONE_FOLDER,
    LOCAL_LOG_FOLDER,
    LOCAL_CONFIG_FOLDER,
]


class AddressAliases(str, enum.Enum):
    """Standard data type enumeration for database type mapping.

    This enum provides a clean, consistent way to specify data types
    across all database platforms, eliminating the mixed approach of
    NumPy types, Python types, and string identifiers.
    """

    # String types
    REFERENCE_ID = "reference_id"
    STREET_ADDRESS = "street_address"
    CITY = "city"  # Generic name; actual column name varies by country
    STATE = "state"
    ZIP_CODE = "zip_code"  # Generic name; actual column name varies by country
    FULL_ADDRESS = "full_address"
    APN = "apn"
    FIPS_CODE = "fips_code"
    OWNER_NAME_1 = "owner_name_1"
    OWNER_NAME_2 = "owner_name_2"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    NORMALIZED_FULL_ADDRESS = "normalized_full_address"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class LogLevel(str, enum.Enum):
    """Log Level"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class AppCode(str, enum.Enum):
    """AppCode - Application code."""

    CLIP = "clip"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class AppSchemaID(str, enum.Enum):
    """Application schema identifiers."""

    CLIP_INPUT = "cotality_app_clip_input"
    CLIP_OUTPUT = "cotality_app_clip_output"
    APP_CONFIG = "cotality_app_config"


class FileFormat(str, enum.Enum):
    """File format types for data export and upload."""

    CSV = "csv"
    PARQUET = "parquet"
    AVRO = "avro"
    JSON = "json"
    JSONL = "jsonl"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class FileCompression(str, enum.Enum):
    """File format types for data export and upload."""

    GZIP = "gzip"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(init=True, frozen=False)
class CSVConfig(DataClassJsonMixin):
    """CSVConfig - CSV Configuration."""

    header: bool = True
    separator: str = "\t"
    encoding: str = "UTF-8"
    escape: str = ""
    quote: str = ""
    escape_quote: bool = False


@dataclass(init=True, frozen=False)
class APIResponse(DataClassJsonMixin):
    """API Response."""

    api: str = "Unknown"
    request_id: str = "Unknown"
    success: bool = False
    error_message: str = "Unknown"
    status_code: int = 0
    response_text: str = ""
    output_counts: int = 0


# ============== Violations
class FieldViolationType(str, enum.Enum):
    """FieldViolationType - Violation type."""

    REQUIRED = "required"
    INVALID_VALUE = "value"
    WRONG_DATA_TYPE = "type"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass
class FieldViolation:
    """FieldViolation - Field violation."""

    field: str
    type: FieldViolationType
    message: str | None = ""


# ============== Status & Event
class StatusCode(str, enum.Enum):
    """StatusCode - Status code"""

    WAITING = "waiting"
    STARTING = "starting"
    STARTED = "started"
    RUNNING = "running"
    FINISHING = "finishing"
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"
    CANCELED = "canceled"

    def __str__(self):
        """
        Returns:
            str: String
        """
        return str(self.value)


class Country(str, enum.Enum):
    """Region."""

    US = "US"
    AU = "AU"
    NZ = "NZ"
    GB = "GB"
    UK = "UK"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class Locale(str, enum.Enum):
    """Region."""

    EN_US = "en_US"
    EN_AU = "en_AU"
    EN_NZ = "en_NZ"
    EN_GB = "en_GB"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)

    @property
    def language(self):
        """Return locale.

        Returns:
            str: Locale
        """
        return self.value.split("_")[0]

    @property
    def country_code(self) -> Country:
        """Return country.

        Returns:
            str: Country
        """
        return Country(self.value.split("_")[1])

    @property
    def date_format(self) -> str:
        """Return date format.

        Returns:
            str: Date format
        """
        match self.country_code:
            case Country.US:
                return "%m/%d/%Y"
            case Country.AU | Country.NZ | Country.GB | Country.UK:
                return "%d/%m/%Y"
            case _:
                raise ClgxException(
                    error=CommonErrorCodes.GEN_INVALID_PARAMETER,
                    parameters={"name": "locale"},
                    message=f"Unsupported country code: {self.country_code} for date format",
                )


class Environment(str, enum.Enum):
    """Environment - Environment."""

    DEV = "dev"
    INT = "int"
    UAT = "uat"
    PROD = "prd"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


# ======================== Platform ==================
class PlatformType(str, enum.Enum):
    """PlatformType - Violation type."""

    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    BIGQUERY = "bigquery"  # Bigquery

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(frozen=False)
class PlatformConfig(DataClassJsonMixin):
    """Platform configuration.

    Args:
        frozen (bool): Frozen
    """

    platform_type: PlatformType = PlatformType.SNOWFLAKE
    locale: Locale = Locale.EN_US
    environment: Environment = Environment.PROD
    # Permissions
    inside_native_platform: bool = True
    has_access_to_external_integration: bool = False
    can_manage_secret: bool = False
    is_single_thread: bool = False

    def __post_init__(self):
        """Post init."""
        # Simplify enum conversion using the _ensure_enum helper
        self.platform_type = self._ensure_enum(
            self.platform_type, PlatformType, "platform_type"
        )
        self.locale = self._ensure_enum(self.locale, Locale, "locale")
        self.environment = self._ensure_enum(
            self.environment, Environment, "environment"
        )

        # locale.setlocale(locale.LC_ALL, self.locale.value)
        try:
            locale.setlocale(locale.LC_ALL, self.locale.value)
        except locale.Error:
            locale.setlocale(locale.LC_ALL, "C")

    @staticmethod
    def _ensure_enum(value, enum_cls, field_name):
        if isinstance(value, enum_cls):
            return value
        try:
            return enum_cls(value)
        except ValueError as exc:
            raise ClgxException(
                error=CommonErrorCodes.GEN_INVALID_PARAMETER,
                parameters={"name": "locale"},
                message=f"Invalid {field_name}: {value!r}",
                cause=exc,
            ) from exc


@dataclass(init=True, frozen=False)
class UserContext(DataClassJsonMixin):
    """User context."""

    platform_type: PlatformType = PlatformType.SNOWFLAKE
    organization: str = "organization"
    app_id: str = "app_id"
    user_id: str = "user_id"
    user_name: str = "user_name"
    user_email: str = "user_email"
    role: str = "role"

    def create_standard_headers(
        self,
        request_id: str = uuid.uuid4().hex,
        content_type: str = "",
        accept: str = "",
    ) -> dict:
        """Set headers with user context.

        Args:
            request_id (str): Request ID
            content_type (str): Content type
            accept (str): Accept header
        """
        headers = {}
        headers[constants.HEADER_ORGANIZATION_ID] = self.organization
        headers[constants.HEADER_SOURCE_APP_ID] = f"{self.platform_type}-{self.app_id}"
        headers[constants.HEADER_SOURCE_APP_REQUEST_ID] = request_id
        headers[constants.HEADER_SOURCE_APP_USER_ID] = self.user_id
        if content_type:
            headers[constants.HEADER_CONTENT_TYPE] = content_type
        if accept:
            headers[constants.HEADER_ACCEPT] = accept
        return headers
