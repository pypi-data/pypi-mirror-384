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
"""Clip Application Configuration"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from dataclasses_json import DataClassJsonMixin

from ....core.clgxtyping import FileFormat
from ....core.interfaces.database import DatabaseClient
from ....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from ....core.interfaces.table import Table
from ..typing import COTALITY_APP_ROLE

PRIMARY_KEY_VALUE = "id"


class Columns(Enum):
    """Column constants for app_config table."""

    ID = "id"
    AUTOMATION_HARD_LIMIT = "automation_hard_limit"
    APP_HARD_LIMIT = "app_hard_limit"
    MAX_INVALID_PERCENTAGE = "max_invalid_percentage"
    NEXT_RETRY_INTERVAL = "next_retry_interval"
    MAX_RETRY_ATTEMPTS = "max_retry_attempts"
    FILE_FORMAT = "file_format"
    TEXT_DELIMITER = "text_delimiter"

    def __str__(self):
        """Return string representation of the column name."""
        return self.value


@dataclass(init=True, frozen=False)
class AppConfig(DataClassJsonMixin):
    """Clip configuration dataclass model.

    This dataclass represents the structure of clip configuration data
    with business-friendly field names that map to database columns.
    """

    id = PRIMARY_KEY_VALUE
    # === CONFIGURATION SETTINGS ===
    automation_hard_limit: int = (
        50000000  # Hard limit of how many clip records for automation job
    )
    app_hard_limit: int = (
        1000000  # Application hard limit of how many clip records to process
    )
    max_invalid_percentage: int = (
        10  # Stop if number of invalid input records exceed this limit
    )
    next_retry_interval: int = 30  # How many days to retry. Example 30 days
    max_retry_attempts: int = 12  # Maximum number of retry. Example: 12 (1 year)
    file_format: FileFormat = FileFormat.CSV  # File format for input/output files
    text_delimiter: str = "\t"  # Text delimiter for CSV files


class AppConfigTable(Table[AppConfig]):
    """Table definition for clip configuration management.

    This table manages clip configuration settings for different input tables.
    Each configuration row defines processing parameters for a specific input table.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        database_name: str,
        schema_name: str,
    ):
        """Initialize AppConfig with database connection and schema.

        Args:
            database_client (DatabaseClient): Database client instance
            database_name (str): Database name
            schema_name (str): Schema name
        """
        table_name = _TABLE_NAME
        super().__init__(
            database_client=database_client,
            dataclass_type=AppConfig,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            columns=_SCHEMA.copy(),
            description="Clip application configuration",
            app_role=COTALITY_APP_ROLE,
        )
        super().create(if_not_exists=True)

    @property
    def table(self):
        """Return this insance."""
        return self

    def init_job(self) -> None:
        """Initialize a clip configuration entry for a new input table.

        If an entry for the input table already exists, this function does nothing.

        """

    def get(self) -> AppConfig:
        """Retrieve the AppConfig for a specific input table.

        Args:
            input_table (str): Input table name without database & schema
        Returns:
            AppConfig: The AppConfig instance for the input table
        """

        app_config = super().get(primary_key_values=PRIMARY_KEY_VALUE)
        if app_config and isinstance(app_config, list):
            app_config = app_config[0]
        else:
            app_config = AppConfig()
        return app_config


# ========= Private areas =========
_TABLE_NAME = "clip_app_config"

# Static schema definition - prevents accidental modification
_SCHEMA: List[ColumnDefinition] = [
    ColumnDefinition(
        name=Columns.ID.value,
        data_type=DataTypeEnum.TEXT,
        description="Primary key",
        nullable=False,
        primary_key=True,
    ),
    ColumnDefinition(
        name=Columns.AUTOMATION_HARD_LIMIT.value,
        data_type=DataTypeEnum.INT64,
        description="Hard limit of how many clip records for automation job",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.APP_HARD_LIMIT.value,
        data_type=DataTypeEnum.INT64,
        description="Application hard limit of how many clip records to process",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.MAX_INVALID_PERCENTAGE.value,
        description="Stop if number of invalid input records exceed this limit",
        data_type=DataTypeEnum.INT64,
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.NEXT_RETRY_INTERVAL.value,
        description="How many days to retry. Example 30 days",
        data_type=DataTypeEnum.INT64,
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.MAX_RETRY_ATTEMPTS.value,
        data_type=DataTypeEnum.INT64,
        description="Maximum number of retry. Example: 12 (1 year)",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.FILE_FORMAT.value,
        data_type=DataTypeEnum.TEXT,
        description="File format for input/output files",
        nullable=True,
    ),
    ColumnDefinition(
        name=Columns.TEXT_DELIMITER.value,
        data_type=DataTypeEnum.TEXT,
        description="Text delimiter for CSV files",
        nullable=True,
    ),
]
