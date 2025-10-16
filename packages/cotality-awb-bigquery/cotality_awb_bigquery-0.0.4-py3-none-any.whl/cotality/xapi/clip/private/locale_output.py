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
"""Clip Output"""
from __future__ import annotations

import enum
from logging import getLogger
from typing import Tuple

from ....core.clgxtyping import AppSchemaID, Country, PlatformType
from ....core.error_codes import CommonErrorCodes
from ....core.exception import ClgxException
from ....core.platform import Platform
from ..typing import ClipMetrics, ClipOutputReferenceColumns, ClipSummaryMetrics
from .clip_job import ClipJob
from .clip_us.output import ClipOutputTable as ClipOutputTableUS

logger = getLogger(__name__)


class Columns(enum.Enum):
    """Column names for the CLIP output table."""

    REFERENCE_ID = "reference_id"
    CLIP_STATUS = "clip_status"
    CLIP_ID = "clip_id"
    CURRENT_HASH = "current_hash"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class ClipOutputTable:
    """Base class for Clip Output Table"""

    def __init__(self, platform: Platform):
        """Initialize the ClipOutputTable instance.

        Args:
            platform (Platform): Platform instance
        """
        self._platform = platform
        self._database_client = platform.database_client

        self._database_name, self._schema_name = platform.get_schema(
            AppSchemaID.CLIP_OUTPUT
        )
        contry_code = platform.config.locale.country_code
        match contry_code:
            case Country.US:
                self._table = ClipOutputTableUS(
                    database_client=platform.database_client,
                    database_name=self._database_name,
                    schema_name=self._schema_name,
                    table_name="clip_output",
                )
            case _:
                raise ClgxException(
                    CommonErrorCodes.CLIP_APP_CONFIG,
                    message=f"ClipOutputTable is not implemented for country code: {contry_code}",
                )

    @property
    def table(self):
        """Get the Clip output table.

        Returns:
            ClipOutputTableUS: Clip output table instance
        """
        return self._table

    def init_job(self, input_table: str) -> None:
        """Initialize a clip output entry for a new input table.

        If an entry for the input table already exists, this function does nothing.

        Args:
            input_table (str): Input table name without database & schema
        """
        _, _, input_table_only = self._table.database_client.parse_table(input_table)
        table_name = self._table.get_table_name(input_table_only)
        self._table.create(table_name=table_name, if_not_exists=True)

    def get_clip_metrics(self, table_name: str) -> ClipMetrics:
        """Get the Clip metrics for a given table.

        Args:
            table_name (str): Name of the table

        Returns:
            ClipMetrics: Clip metrics for the table
        """
        clip_metric = ClipMetrics()
        clip_metric.input_metrics.clip_counts = self._table.row_counts(
            table_name=table_name
        )
        clip_metric.clip_summary_metric = self._table.aggregate_clip_metric(
            table_name=table_name
        )

        table_name = self._table.get_table_name(table_name)
        sql = _SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SQL.get(
            self._platform.config.platform_type, ""
        ).format(ref_output_table=table_name)
        ref_counts = self._database_client.query_to_dict(sql)[0]
        for field, value in ref_counts.items():
            value = 0 if value is None else value
            setattr(clip_metric.input_metrics, field, value)

        clip_metric.input_metrics.total_input_counts = (
            clip_metric.input_metrics.clip_counts
            + clip_metric.input_metrics.non_clip_counts
            + clip_metric.input_metrics.invalid_counts
        )

        return clip_metric

    def get_temp_tables(
        self, input_table_name: str, return_full_name: bool = True
    ) -> Tuple[str, str]:
        """Get the list of temporary tables created by the Clip output table.

        Returns:
            Tuple[str, str]: dedup_table_name, full_table_name
        """

        dedup_table_name = f"{input_table_name}_temp_dedup"
        full_table_name = f"{input_table_name}_temp_full"
        if return_full_name:
            dedup_table_name = self._database_client.full_table_name(
                database=self._database_name,
                schema=self._schema_name,
                table=dedup_table_name,
            )
            full_table_name = self._database_client.full_table_name(
                database=self._database_name,
                schema=self._schema_name,
                table=full_table_name,
            )
        return (dedup_table_name, full_table_name)

    def create_temp_tables(self, table_name: str):
        """Create a temporary table with the same schema as the Clip output table.

        Args:
            table_name (str): Name of the temporary table to create
        """
        dedup_table_name, full_table_name = self.get_temp_tables(table_name)
        self._table.drop(table_name=dedup_table_name)
        self._table.drop(table_name=full_table_name)
        self._table.create(table_name=dedup_table_name, if_not_exists=True)
        self._table.create(table_name=full_table_name, if_not_exists=True)

    def update_clip_metrics(self, clip_job: ClipJob) -> None:
        """Update the Clip metrics in the Clip job.

        Args:
            clip_job (ClipJob): The Clip job to update
        """
        dedup_table_name, _ = self.get_temp_tables(
            clip_job.input_table, return_full_name=True
        )
        logger.info("Calculate clip metrics from dedup: %s", dedup_table_name)

        try:
            row_counts = self._table.row_counts(dedup_table_name)
            if row_counts > 0:
                sql = f"""
SELECT COUNT({Columns.CLIP_ID}) AS clipped, COUNT(*) - COUNT({Columns.CLIP_ID}) AS not_clipped FROM {dedup_table_name}"""
                count_results = self._database_client.query_to_dict(sql)[0]
                clip_job.clip_metrics.input_metrics.non_clip_counts = count_results.get(
                    "not_clipped", 0
                )
                clip_job.clip_metrics.input_metrics.clip_counts = count_results.get(
                    "clipped", 0
                )
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": clip_job.input_table},
                message="Failed to update Clip metrics",
                cause=e,
            ) from e

    def consolidate_clip_output_table(
        self,
        input_table: str,
        full_reference_table: str,
        ref_input_column_names: list[str],
    ) -> None:
        """Consolidate the Clip output table from the temporary table to the final output table.

        Args:
            input_table (str): Name of the input table
            full_reference_table (str): Full name of the reference input table
            ref_input_column_names (list[str]): List of input column names
        """
        self._update_dedup_table_with_input_columns(
            input_table=input_table,
            full_reference_table=full_reference_table,
            ref_input_column_names=ref_input_column_names,
        )
        self._create_full_table_from_dedup(
            input_table=input_table,
            full_reference_table=full_reference_table,
        )
        self._delete_clip_records_from_clip_output_table(input_table=input_table)
        self._insert_clip_records_to_clip_output_table(input_table=input_table)

    def _update_dedup_table_with_input_columns(
        self,
        input_table: str,
        full_reference_table: str,
        ref_input_column_names: list[str],
    ) -> None:
        """Update the dedup table with input columns from the input table.

        Args:
            input_table (str): Name of the input table
            full_reference_table (str): Full name of the reference input table
            ref_input_column_names (list[str]): List of input column names from the reference table
        """

        sql = ""
        params = []
        try:
            full_dedup_table_name, _ = self.get_temp_tables(
                input_table, return_full_name=True
            )
            logger.info(
                "Update dedup table: %s with input columns: %s",
                full_dedup_table_name,
                ref_input_column_names,
            )
            set_parts = []
            for name in ref_input_column_names:
                set_parts.append(f"{name} = ref.{name}")
            set_clause = ", ".join(set_parts)

            # Build the aggregation for the GROUP BY query
            agg_parts = [
                f"ANY_VALUE({name}) AS {name}" for name in ref_input_column_names
            ]
            agg_parts.append("current_hash")
            agg_clause = ", ".join(agg_parts)
            sql = UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL[
                self._platform.config.platform_type
            ].format(
                full_dedup_table=full_dedup_table_name,
                full_reference_table=full_reference_table,
                set_clause=set_clause,
                agg_clause=agg_clause,
            )
            logger.debug("Update dedup table SQL: %s", sql)
            self._database_client.execute(sql)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": full_dedup_table_name},
                message=(
                    "Failed to update dedup table with input columns."
                    f"SQL: {sql}, Params: {params}"
                ),
                cause=e,
            ) from e

    def _create_full_table_from_dedup(
        self, input_table: str, full_reference_table: str
    ) -> None:
        """Insert clip records into the full output table from the dedup table.

        Args:
            input_table (str): Name of the input table
            full_reference_table (str): Full name of the reference input table
            ref_input_column_names (list[str]): List of input column names from the reference table
        """
        sql = ""
        params = []
        try:
            dedup_table_name, full_table_name = self.get_temp_tables(input_table)
            pk, output_columns = self._table.column_names
            pk = pk[0]
            output_column_expression = ", ".join(output_columns)
            dedup_output_columns = [f"dedup.{col}" for col in output_columns]
            dedup_output_column_expression = ", ".join(dedup_output_columns)

            output_columns = ", ".join(output_columns)
            logger.debug(
                "Insert dedup table: %s with input columns: %s",
                dedup_table_name,
                output_column_expression,
            )
            sql = f"""
INSERT INTO {full_table_name} ({pk}, {output_column_expression})
SELECT ref.{pk}, {dedup_output_column_expression}
FROM {dedup_table_name} dedup LEFT JOIN {full_reference_table} ref
ON dedup.{Columns.REFERENCE_ID} = ref.{Columns.CURRENT_HASH}
""".strip()
            logger.debug("Update dedup table SQL: %s", sql)
            self._database_client.execute(sql)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": full_table_name},
                message=(
                    "Failed to insert clip records." f"SQL: {sql}, Params: {params}"
                ),
                cause=e,
            ) from e

    def _delete_clip_records_from_clip_output_table(self, input_table: str) -> None:
        """Delete clip records from the final output table.

        Args:
            input_table (str): Name of the input table
        """
        sql = ""
        params = []
        try:
            _, full_table_name = self.get_temp_tables(
                input_table, return_full_name=True
            )
            final_table_name = self._table.get_table_name(input_table)
            pk, _ = self._table.column_names
            pk = pk[0]
            sql = f"""
DELETE FROM {final_table_name}
WHERE {pk} IN (SELECT {pk} FROM {full_table_name})
""".strip()
            logger.debug("Delete clip records SQL: %s", sql)
            self._database_client.execute(sql)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": final_table_name},
                message=(
                    "Failed to delete clip records." f"SQL: {sql}, Params: {params}"
                ),
                cause=e,
            ) from e

    def _insert_clip_records_to_clip_output_table(self, input_table: str) -> None:
        """Merge clip records from the temporary full table to the final output table.

        Args:
            input_table (str): Name of the input table
        """
        sql = ""
        params = []
        try:
            _, full_table_name = self.get_temp_tables(
                input_table, return_full_name=True
            )
            final_table_name = self._table.get_table_name(input_table)
            pk, output_columns = self._table.column_names
            pk = pk[0]
            output_column_expression = ", ".join(output_columns)
            sql = f"""
INSERT INTO {final_table_name} ({pk}, {output_column_expression})
SELECT {pk}, {output_column_expression}
FROM {full_table_name} src
""".strip()
            logger.debug("Merge clip records SQL: %s", sql)
            self._database_client.execute(sql)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": final_table_name},
                message=(
                    "Failed to merge clip records." f"SQL: {sql}, Params: {params}"
                ),
                cause=e,
            ) from e


# ========== SQL Queries ==========
_SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL = """
SELECT
  SUM(CASE WHEN clip_status = 'invalid' THEN 1 ELSE 0 END) AS invalid_counts,
  SUM(CASE WHEN clip_status = 'not_clipped' THEN 1 ELSE 0 END) AS non_clip_counts
FROM {ref_output_table}
""".strip()

_SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SQL = {
    PlatformType.SNOWFLAKE: _SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _SELECT_INVALID_AND_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
}

__UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL_BQ = """
UPDATE {{full_dedup_table}} AS dedup
SET
    {{set_clause}}
FROM (
    SELECT
        {{agg_clause}}
    FROM {{full_reference_table}}
    GROUP BY {current_hash}
) AS ref
WHERE dedup.{reference_id} = ref.{current_hash};
""".strip().format(
    reference_id=ClipOutputReferenceColumns.REFERENCE_ID.value,
    current_hash=ClipOutputReferenceColumns.CURRENT_HASH.value,
)

__UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL_SNOWFLAKE = """
MERGE INTO {{full_dedup_table}} AS dedup
USING (
    SELECT
        {{agg_clause}}
    FROM {{full_reference_table}}
    GROUP BY {current_hash}
) AS ref
ON dedup.{reference_id} = ref.{current_hash}
WHEN MATCHED THEN
    UPDATE SET
        {{set_clause}}
""".strip().format(
    reference_id=ClipOutputReferenceColumns.REFERENCE_ID.value,
    current_hash=ClipOutputReferenceColumns.CURRENT_HASH.value,
)

UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL = {
    PlatformType.BIGQUERY: __UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL_BQ,
    PlatformType.SNOWFLAKE: __UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL_SNOWFLAKE,
    PlatformType.DATABRICKS: __UPDATE_DEDUP_WITH_INPUT_COLUMNS_SQL_SNOWFLAKE,
}
