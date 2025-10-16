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
"""Clip Configuration Database Interface."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from dataclasses_json import DataClassJsonMixin

from ....core.interfaces.database import DatabaseClient
from ....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from ....core.interfaces.table import Table
from ..typing import COTALITY_APP_ROLE


class Columns(Enum):
    """Column constants for clip_config table."""

    INPUT_TABLE = "input_table"
    BEST_MATCH = "best_match"
    GOOGLE_FALLBACK = "google_fallback"

    def __str__(self):
        """Return string representation of the column name."""
        return self.value


@dataclass(init=True, frozen=False)
class ClipConfig(DataClassJsonMixin):
    """Clip configuration dataclass model.

    This dataclass represents the structure of clip configuration data
    with business-friendly field names that map to database columns.
    """

    # === PRIMARY KEY ===
    input_table: str = ""  # Clip input table without database & schema

    # === CONFIGURATION SETTINGS ===
    best_match: bool = True  # Best match
    google_fallback: bool = False  # Fall back to Google address standardization
    legacy_county_source: bool = False


class ClipConfigTable(Table[ClipConfig]):
    """Table definition for clip configuration management.

    This table manages clip configuration settings for different input tables.
    Each configuration row defines processing parameters for a specific input table.
    """

    def __init__(
        self, database_client: DatabaseClient, database_name: str, schema_name: str
    ):
        """Initialize ClipConfigTable with database connection and schema.

        Args:
            database_client (DatabaseClient): Database client instance
            database_name (str): Database name
            schema_name (str): Schema name
            table_name (str): Not used
            description (str, optional): Table description. Defaults to descriptive text.
            app_role (str, optional): Application role for permissions. Defaults to COTALITY_APP_ROLE.
        """
        table_name = _TABLE_NAME
        super().__init__(
            database_client=database_client,
            dataclass_type=ClipConfig,
            database_name=database_name,
            schema_name=schema_name,
            table_name=table_name,
            columns=_SCHEMA.copy(),
            description="Clip configuration table for managing processing settings",
            app_role=COTALITY_APP_ROLE,
        )
        super().create(if_not_exists=True)

    @property
    def table(self):
        """Return this insance."""
        return self

    def init_job(self, input_table: str) -> None:
        """Initialize a clip configuration entry for a new input table.

        If an entry for the input table already exists, this function does nothing.

        Args:
            input_table (str): Input table name without database & schema
        """

    def get(self, input_table: str) -> ClipConfig:
        """Retrieve the ClipConfig for a specific input table.

        Args:
            input_table (str): Input table name without database & schema
        Returns:
            ClipConfig: The ClipConfig instance for the input table
        """
        _, _, input_table_only = self.database_client.parse_table(input_table)
        clip_config = super().get(primary_key_values=input_table_only)
        if clip_config and isinstance(clip_config, list):
            clip_config = clip_config[0]
        else:
            clip_config = ClipConfig(input_table=input_table_only)
        return clip_config


# ========= Private areas =========
_TABLE_NAME = "clip_config"

# Static schema definition - prevents accidental modification
_SCHEMA: List[ColumnDefinition] = [
    ColumnDefinition(
        name="input_table",
        data_type=DataTypeEnum.TEXT,
        description="Clip input table without database & schema",
        nullable=False,
        primary_key=True,
    ),
    ColumnDefinition(
        name="best_match",
        data_type=DataTypeEnum.BOOLEAN,
        description="Best match",
        nullable=True,
    ),
    ColumnDefinition(
        name="google_fallback",
        data_type=DataTypeEnum.BOOLEAN,
        description="Fall back to Google address standardization",
        nullable=True,
    ),
    ColumnDefinition(
        name="legacy_county_source",
        data_type=DataTypeEnum.BOOLEAN,
        description="Use legacy county source",
        nullable=True,
    ),
]
