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
"""Clip Input"""
from __future__ import annotations

from typing import Tuple

import pandas as pd

from ....core.clgxtyping import AppSchemaID, Country
from ....core.error_codes import CommonErrorCodes
from ....core.exception import ClgxException
from ....core.interfaces.database_types import ColumnDefinition
from ....core.interfaces.table import Table
from ....core.platform import Platform
from ..typing import COTALITY_APP_ROLE, RunStatus
from .clip_job import ClipJob
from .clip_us.input import REQUIRED_CLIP_COLUMNS, ClipInputTableUS


class ClipInputTable:
    """Base class for Clip Input Table"""

    def __init__(self, platform: Platform):
        """Initialize the ClipInputTable instance.

        Args:
            platform (Platform): Platform instance
        """
        self._platform = platform
        self._database_client = platform.database_client

        database_name, schema_name = platform.get_schema(AppSchemaID.CLIP_INPUT)
        contry_code = platform.config.locale.country_code
        match contry_code:
            case Country.US:
                self._table = ClipInputTableUS(
                    database_client=platform.database_client,
                    database_name=database_name,
                    schema_name=schema_name,
                    table_name="clip_input",
                )
            case _:
                raise ClgxException(
                    error=CommonErrorCodes.CLIP_APP_CONFIG,
                    message=f"Unsupported country code: {contry_code} for ClipInputTable",
                )

    @property
    def table(self):
        """Get the Clip input table.

        Returns:
            Table: Clip input table
        """
        return self._table

    def get_clip_missing_columns(self, table_name: str) -> list[str]:
        """Validate the schema of the Clip input table.
        Args:
            table (str): Input table name

        Returns:
            List[str]: List of missing columns
        """
        table_column_names = self._database_client.get_column_names(
            self._table.get_table_name(table_name)
        )
        pk, expected_column_names = self._table.column_names
        expected_column_names = (
            pk + expected_column_names
        )  # Ensure PK is included in the check
        return [col for col in expected_column_names if col not in table_column_names]

    def validate_schema(self, table_name: str) -> None:
        """Validate the schema of the Clip input table.

        Args:
            table (str): Input table name
        """
        table_name = self._table.get_table_name(table_name)
        names = self._database_client.get_column_names(table_name)
        missing_columns = [
            col for col in self._table.required_clip_columns if col not in names
        ]
        if missing_columns or len(missing_columns) > 0:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_INVALID_CLIP_INPUT_SCHEMA,
                message=f"Input table {table_name} is missing required columns: {', '.join(missing_columns)}",
            )
        self.validate_primary_key_uniqueness(table_name)

    def validate_primary_key_uniqueness(self, table_name: str) -> None:
        """Ensure that the reference_id column in the table has all unique values.

        Args:
            table_name (str): Input table name

        Raises:
            ClgxException: If reference_id values are not unique.
        """
        table_name = self._table.get_table_name(table_name)
        df = self._database_client.query_to_pandas(
            f"SELECT {REQUIRED_CLIP_COLUMNS[0]} FROM {table_name}"
        )
        unique_count = df[REQUIRED_CLIP_COLUMNS[0]].nunique(dropna=False)
        total_count = self._database_client.row_counts(table_name)
        if unique_count != total_count:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_DUPLICATE_CLIP_INPUT_PRIMARY_KEY,
                parameters={"name": REQUIRED_CLIP_COLUMNS[0]},
                message=f"Input table {table_name} has non-unique values in {REQUIRED_CLIP_COLUMNS[0]} column.",
            )
