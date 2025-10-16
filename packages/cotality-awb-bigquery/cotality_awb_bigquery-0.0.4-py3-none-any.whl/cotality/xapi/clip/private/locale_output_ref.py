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
"""Clip Output Reference Table"""
from __future__ import annotations

from logging import getLogger
from typing import Tuple

from ....core.clgxtyping import AddressAliases, AppSchemaID, Country, PlatformType
from ....core.error_codes import CommonErrorCodes
from ....core.exception import ClgxException
from ....core.interfaces.database_types import ColumnDefinition, DataTypeEnum
from ....core.platform import Platform
from ....core.utils.misc import datetime_to_int
from ..typing import (
    INPUT_COLUMNS_GROUP,
    META_COLUMNS_GROUP,
    ClipOutputReferenceColumns,
    PropertyClipStatus,
)
from .clip_us.output_ref import ClipOutputReferenceTableUS

logger = getLogger(__name__)


class ClipOutputReferenceTable:
    """Base class for Clip Output Reference Table"""

    def __init__(self, platform: Platform):
        """Initialize the ClipOutputTable instance.

        Args:
            platform (Platform): Platform instance
        """
        self._platform = platform
        self._database_client = platform.database_client

        self._database_name, self._schema_name = platform.get_schema(
            AppSchemaID.APP_CONFIG
        )
        contry_code = platform.config.locale.country_code
        match contry_code:
            case Country.US:
                self._table = ClipOutputReferenceTableUS(
                    database_client=platform.database_client,
                    database_name=self._database_name,
                    schema_name=self._schema_name,
                    table_name="unknon",
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
        """Initialize a clip reference entry for a new input table.

        If an entry for the input table already exists, this function does nothing.

        Args:
            input_table (str): Input table name without database & schema
        """
        table_name = self._table.get_table_name(input_table)
        self._table.create(table_name=table_name, if_not_exists=True)

    def get_temp_table_name(self, input_table: str) -> str:
        """Get the temporary table name for the input table.

        Args:
            input_table (str): Input table name without database & schema
        Returns:
            str: Temporary table name
        """
        tmp_table_name = self._table.get_table_name(f"{input_table}_tmp")
        return tmp_table_name

    @property
    def input_colmns(self) -> list[ColumnDefinition]:
        """Get the input columns group.

        Returns:
            list: List of input column definitions
        """
        return self._table.columns_by_group.get(INPUT_COLUMNS_GROUP, [])

    @property
    def input_colmn_names(self) -> list[str]:
        """Get the input columns group.

        Returns:
            list: List of input column definitions
        """
        return [col.name for col in self.input_colmns]

    def delete_orphan_input_records(self, full_input_table: str) -> None:
        """Detect delete input records in the reg_output table but not in the input table.

        Args:
            full_input_table (str): Full input table name
        """
        sql = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(full_input_table)
            logger.info("Deleting orphan input records from: %s", full_ref_output_table)
            sql = _DELETE_STALE_OUTPUT_REF_RECORDS_SQL[
                self._platform.config.platform_type
            ].format(
                full_input_table=full_input_table,
                full_ref_output_table=full_ref_output_table,
                pk=ClipOutputReferenceColumns.REFERENCE_ID.value,
            )
            self._database_client.execute(sql)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error deleting stale records."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def add_new_input_records(self, full_input_table: str, limit: int = 0) -> None:
        """Add new input records to the reference output table.

        Args:
            full_input_table (str): Full input table name
        """
        sql = ""
        full_ref_output_table = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(full_input_table)
            logger.info("Adding new input records to: %s", full_ref_output_table)

            column_names_by_group = self._table.column_names_by_group
            meta_column_names = column_names_by_group.get(META_COLUMNS_GROUP, [])
            input_column_names, cleaned_input_expressions, cleaned_input_columns, _ = (
                self._prepare_input_columns()
            )

            input_column_names = ", ".join(input_column_names)
            meta_column_names = ", ".join(meta_column_names)
            cleaned_input_columns = ", ".join(cleaned_input_columns)

            next_retry = datetime_to_int(day_offset=-1)
            sql = _INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SQL[
                self._platform.config.platform_type
            ].format(
                full_input_table=full_input_table,
                full_ref_output_table=full_ref_output_table,
                input_column_names=input_column_names,
                cleaned_input_expressions=", ".join(cleaned_input_expressions),
                cleaned_input_columns=cleaned_input_columns,
                meta_column_names=meta_column_names,
            )
            if limit > 0:
                sql = f"{sql} LIMIT {limit}"
            params = [
                PropertyClipStatus.NEW.value,
                next_retry,
            ]
            self._database_client.execute(sql=sql, params=params)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error inserting new records."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def update_input_changed_records(self, full_input_table: str) -> None:
        """Update changed input records in the reference output table.

        Args:
            full_input_table (str): Full input table
        """
        sql = ""
        full_ref_output_table = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(full_input_table)
            logger.info("Detecting updated input records from: %s", full_input_table)
            _, cleaned_input_expressions, _, set_clauses = self._prepare_input_columns()
            cleaned_input_expressions = ", ".join(cleaned_input_expressions)
            # Build the optimized subquery-based update
            sql = _UPDATE_ALL_OUTPUT_REF_SQL[
                self._platform.config.platform_type
            ].format(
                full_input_table=full_input_table,
                full_ref_output_table=full_ref_output_table,
                cleaned_input_expressions=cleaned_input_expressions,
                set_clauses=", ".join(set_clauses),
            )

            self._database_client.execute(sql)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error updating changed records."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def update_normalized_full_address(self, full_input_table: str) -> None:
        """Update the normalized full address in the reference table."""
        self._update_normalized_full_address(full_input_table)
        self._update_current_hash(full_input_table)
        self._update_clip_status_for_updated_records(full_input_table)

    def validate_required_clip_data(self, input_table: str) -> Tuple[int, int]:
        """Validate that required Clip data is present in the reference output table.

        Args:
            input_table (str): Input table name
        Returns:
            Tuple[int, int]: Before and after row counts of invalid records
        """
        sql = ""
        full_ref_output_table = ""
        params = [PropertyClipStatus.INVALID.value]
        try:
            full_ref_output_table = self._table.get_table_name(input_table)
            logger.info(
                "Validating required clip columns from table: %s", full_ref_output_table
            )

            sql = f"{ClipOutputReferenceColumns.CLIP_STATUS.value} = ?"
            params = [PropertyClipStatus.INVALID.value]
            before_row_counts = self._table.get_row_counts(
                table_name=full_ref_output_table, conditions=sql, params=params
            )

            # Validate input data combinations
            self.validate_input_data(input_table)

            sql = _CLIP_COLUMN_VALIDATION_SQL[
                self._platform.config.platform_type
            ].format(
                full_ref_output_table=full_ref_output_table,
            )
            params = [PropertyClipStatus.INVALID.value]
            self._database_client.execute(sql=sql, params=params)

            sql = f"{ClipOutputReferenceColumns.CLIP_STATUS.value} = ?"
            params = [PropertyClipStatus.INVALID.value]
            after_row_counts = self._table.get_row_counts(
                table_name=full_ref_output_table, conditions=sql, params=params
            )
            return before_row_counts, after_row_counts

        except ClgxException as ex:
            raise ex
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": input_table},
                message=(
                    f"Error validating required Clip columns."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def validate_input_data(self, input_table: str) -> None:
        """Validate input data combinations.
        Args:
            input_table (str): Input table name
        """
        sql = ""
        params = [PropertyClipStatus.INVALID.value]
        try:
            full_ref_output_table = self._table.get_table_name(input_table)
            logger.info(
                "Validating input data combinations from table: %s",
                full_ref_output_table,
            )

            sql = _VALIDATE_INPUT_DATA_COMBINATIONS_SQL[
                self._platform.config.platform_type
            ].format(
                full_ref_output_table=full_ref_output_table,
            )
            self._database_client.execute(sql=sql, params=params)

        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": input_table},
                message=(
                    f"Error validating input data combinations."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def collect_clip_input_records(
        self, input_table: str, limit: int = 0
    ) -> Tuple[int, str, dict[str, str]]:
        """Collect input records that are ready for Clip processing.

        Args:
            input_table (str): Input table name
            limit (int, optional): Limit the number of records. Defaults to 0 (no limit).
        Returns:
            Tuple[int, str, dict[str, str]]: Number of records, SQL query string, clip input mappings
        """
        try:
            collect_sql, clip_input_mappings, pk, columns = (
                self._collect_clip_input_records_sql(input_table, limit)
            )
            row_counts, full_tmp_ref_output_table = (
                self._save_collect_clip_input_records(input_table, collect_sql)
            )
            select_sql = f"SELECT {pk}, {columns} FROM {full_tmp_ref_output_table}"
            return row_counts, select_sql, clip_input_mappings
        except ClgxException as ex:
            raise ex
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": input_table},
                message=(
                    f"Error collecting Clip input records."
                    f"Table:{input_table}, SQL: {collect_sql}, Mapping:{clip_input_mappings}"
                ),
                cause=ex,
            ) from ex

    def update_reference_table(
        self,
        input_table: str,
        tmp_full_table_name: str,
        next_retry_interval: int,
        max_retry_attempts: int,
    ) -> None:
        """Update the reference table with clipped and non-clipped records.

        Args:
            input_table (str): Input table name
            tmp_full_table_name (str): Temporary full table name
            next_retry_interval (int): Next retry interval in days for non-clipped records
            max_retry_attempts (int): Maximum number of retry attempts for non-clipped records
        """
        self._update_reference_table_with_clipped_records(
            input_table, tmp_full_table_name
        )
        self._update_reference_table_with_non_clipped_records(
            input_table, tmp_full_table_name, next_retry_interval, max_retry_attempts
        )

    # ================ Public Methods =================
    def _collect_clip_input_records_sql(
        self, input_table: str, limit: int = 0
    ) -> Tuple[str, dict[str, str], str, str]:
        """Collect input records that are ready for Clip processing.

        Args:
            input_table (str): Input table name
            limit (int, optional): Limit the number of records. Defaults to 0 (no limit).
        Returns:
            Tuple[str, dict[str, str], str, str]: collect SQL, clip input mappings, reference_id column name, input column names
        """
        sql = ""
        full_ref_output_table = ""
        clip_input_mappings = {}
        try:
            full_ref_output_table = self._table.get_table_name(input_table)
            logger.info(
                "Return SQL to collect which records to process from table: %s",
                full_ref_output_table,
            )
            clip_column_names = self._table.get_column_names_from_aliases_as_dict(
                [
                    AddressAliases.NORMALIZED_FULL_ADDRESS.value,
                    AddressAliases.APN.value,
                    AddressAliases.FIPS_CODE.value,
                    AddressAliases.OWNER_NAME_1.value,
                    AddressAliases.OWNER_NAME_2.value,
                    AddressAliases.LATITUDE.value,
                    AddressAliases.LONGITUDE.value,
                ]
            )

            input_column_names = []

            # Address
            full_address = clip_column_names[
                ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value
            ]
            input_column_names.append(full_address)
            clip_input_mappings["fullAddress"] = full_address

            # APN
            apn = clip_column_names[AddressAliases.APN.value]
            if apn:
                input_column_names.append(apn)
                clip_input_mappings["apn"] = apn

            # FIPS Code
            fip_code = clip_column_names[AddressAliases.FIPS_CODE.value]
            if fip_code:
                input_column_names.append(fip_code)
                clip_input_mappings["countyCode"] = fip_code

            # Owner 1
            owner_1 = clip_column_names[AddressAliases.OWNER_NAME_1.value]
            owner_2 = clip_column_names[AddressAliases.OWNER_NAME_2.value]
            if owner_1 and not owner_2:
                input_column_names.append(owner_1)
                input_column_names.append(owner_2)
                clip_input_mappings["owners"] = f'["{owner_1}", "{owner_2}"]'

            # Latitude and
            latitude = clip_column_names[AddressAliases.LATITUDE.value]
            longitude = clip_column_names[AddressAliases.LONGITUDE.value]
            if latitude and longitude:
                input_column_names.append(latitude)
                input_column_names.append(longitude)
                clip_input_mappings["latitude"] = latitude
                clip_input_mappings["longitude"] = longitude

            input_column_names = ", ".join(input_column_names)
            now = datetime_to_int()
            # Use ROW_NUMBER() to get distinct rows based on current_hash column
            # This works across Snowflake, Databricks, and BigQuery
            sql = f"""
SELECT {ClipOutputReferenceColumns.CURRENT_HASH.value} AS {ClipOutputReferenceColumns.REFERENCE_ID.value}, {input_column_names}
FROM (
    SELECT {ClipOutputReferenceColumns.CURRENT_HASH.value} , {input_column_names},
        ROW_NUMBER() OVER (PARTITION BY {ClipOutputReferenceColumns.CURRENT_HASH.value} ORDER BY {ClipOutputReferenceColumns.REFERENCE_ID.value}) as rn
    FROM {full_ref_output_table}
    WHERE {ClipOutputReferenceColumns.NEXT_RETRY_AT.value} > 0 and {ClipOutputReferenceColumns.NEXT_RETRY_AT.value} < {now}
) ranked
WHERE rn = 1"""
            if limit > 0:
                sql += f" LIMIT {limit}"
            logger.debug("Collecting Clip input records using SQL: %s", sql)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": input_table},
                message=(
                    f"Error preparing SQL to collect Clip input records from table: {full_ref_output_table}."
                    f"SQL: {sql}, Mapping:{clip_input_mappings}"
                ),
                cause=ex,
            ) from ex

        return (
            sql,
            clip_input_mappings,
            ClipOutputReferenceColumns.REFERENCE_ID.value,
            input_column_names,
        )

    def _save_collect_clip_input_records(
        self, input_table: str, sql: str
    ) -> Tuple[int, str]:
        """Collect input records that are ready for Clip processing.

        Args:
            input_table (str): Input table name
        Returns:
            Tuple[int, str]: Number of records, temporary full table name
        """
        full_tmp_ref_output_table = ""
        params = []
        try:
            full_tmp_ref_output_table = self.get_temp_table_name(input_table)
            sql = f"CREATE OR REPLACE TABLE {full_tmp_ref_output_table} AS {sql}"
            self._database_client.execute(sql=sql)
            row_counts = self._database_client.row_counts(
                table=full_tmp_ref_output_table
            )
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": input_table},
                message=(
                    f"Error collecting Clip input records."
                    f"Table:{full_tmp_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex
        return row_counts, full_tmp_ref_output_table

    def _update_reference_table_with_clipped_records(
        self, input_table: str, tmp_full_table_name: str
    ) -> None:
        """Update the reference table with clipped records

        Args:
            input_table (str): Input table name
            tmp_full_table_name (str): Temporary full table name
        """
        sql = ""
        full_ref_output_table = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(input_table)
            logger.info(
                "Updating reference table: %s from temp table: %s",
                full_ref_output_table,
                tmp_full_table_name,
            )

            # Update current_hash to '' for records that were processed
            sql = _UPDATE_WITH_CLIPPED_RECORDS[
                self._platform.config.platform_type
            ].format(
                ref_output_table=full_ref_output_table, clip_output=tmp_full_table_name
            )
            params = [
                PropertyClipStatus.CLIPPED.value,  # clip_status
            ]
            self._database_client.execute(sql=sql, params=params)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": input_table},
                message=(
                    f"Error updating reference table with clipped results"
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def _update_reference_table_with_non_clipped_records(
        self,
        input_table: str,
        tmp_full_table_name: str,
        next_retry_interval: int,
        max_retry_attempts: int,
    ) -> None:
        """Update the reference table with non-clipped records.

        Args:
            input_table (str): Input table name
            tmp_full_table_name (str): Temporary full table name
            next_retry_interval (int): Next retry interval in days for non-clipped records
            max_retry_attempts (int): Maximum number of retry attempts for non-clipped records
        """
        sql = ""
        full_ref_output_table = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(input_table)
            logger.info(
                "Updating reference table: %s from temp table: %s",
                full_ref_output_table,
                tmp_full_table_name,
            )

            # Update current_hash to '' for records that were processed
            sql = _UPDATE_WITH_NOT_CLIPPED_RECORDS[
                self._platform.config.platform_type
            ].format(
                ref_output_table=full_ref_output_table, clip_output=tmp_full_table_name
            )
            next_retry_at = datetime_to_int(day_offset=next_retry_interval)
            params = [
                PropertyClipStatus.NOT_CLIPPED.value,  # clip_status
                max_retry_attempts,  # retry_attempts
                next_retry_at,  # next_retry_at
            ]
            self._database_client.execute(sql=sql, params=params)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": input_table},
                message=(
                    f"Error updating reference table with clipped results"
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def _prepare_input_columns(self) -> Tuple[list, list, list, list]:
        """Update current hash using optimized subquery approach for better performance

        Returns:
            Tuple[str, str, list, list, list, list]: pk, property_columns, cleaned_expressions,
                cleaned_columns, set_clauses
        """
        # logger.info("Preparing Hash columns for input records...")

        columns_by_group = self._table.columns_by_group
        input_columns = columns_by_group.get(INPUT_COLUMNS_GROUP, [])

        # Build cleaned expressions for subquery (computed once)
        input_column_names = []
        cleaned_input_expressions = []
        cleaned_input_columns = []
        set_clauses = []

        for col in input_columns:
            input_column_names.append(col.name)
            if col.data_type in [DataTypeEnum.STRING, DataTypeEnum.TEXT]:
                cleaned_expr = self._database_client.clean_text_format(col.name)
            else:
                cleaned_expr = col.name

            cleaned_input_expressions.append(f"{cleaned_expr} AS {col.name}")
            cleaned_input_columns.append(f"cleaned.{col.name}")
            set_clauses.append(f"{col.name} = cleaned.{col.name}")

        return (
            input_column_names,
            cleaned_input_expressions,
            cleaned_input_columns,
            set_clauses,
        )

    def _hash_input_columns(self) -> str:
        """Generate hash expression for input columns.

        Args:
            input_columns (List[ColumnDefinition]): List of input column definitions
        """
        hash_columns = self._table.get_column_names_from_aliases_as_dict(
            [
                AddressAliases.NORMALIZED_FULL_ADDRESS.value,
                AddressAliases.APN.value,
                AddressAliases.FIPS_CODE.value,
                AddressAliases.OWNER_NAME_1.value,
                AddressAliases.OWNER_NAME_2.value,
                AddressAliases.LATITUDE.value,
                AddressAliases.LONGITUDE.value,
            ]
        )
        hash_parts = []
        hash_parts.append(
            f"COALESCE({hash_columns[AddressAliases.NORMALIZED_FULL_ADDRESS.value]}, '')"
        )
        hash_parts.append(f"COALESCE({hash_columns[AddressAliases.APN.value]}, '')")
        hash_parts.append(
            f"COALESCE({hash_columns[AddressAliases.FIPS_CODE.value]}, '')"
        )
        hash_parts.append(
            f"COALESCE({hash_columns[AddressAliases.OWNER_NAME_1.value]}, '')"
        )
        hash_parts.append(
            f"COALESCE({hash_columns[AddressAliases.OWNER_NAME_2.value]}, '')"
        )
        hash_parts.append(
            f"COALESCE({self._database_client.cast_to_string(AddressAliases.LATITUDE.value)}, '')"
        )
        hash_parts.append(
            f"COALESCE({self._database_client.cast_to_string(AddressAliases.LONGITUDE.value)}, '')"
        )
        # Platform-specific hash values formatting
        if self._platform.config.platform_type == PlatformType.BIGQUERY:
            # BigQuery uses || for concatenation with pipe separators
            hash_values_expression = ' || "|" || '.join(hash_parts)
        else:
            # Snowflake/Databricks use comma separation for HASH function
            hash_values_expression = ", ".join(hash_parts)
        return hash_values_expression

    def _update_normalized_full_address(self, full_input_table: str) -> None:
        """Update the normalized full address in the reference table."""
        sql = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(full_input_table)
            logger.info(
                "Updating normalized_full_address in the reference table: %s",
                full_ref_output_table,
            )

            # Update normalized_full_address using full_address if available, otherwise construct from address components
            address_columns = self._table.get_column_names_from_aliases_as_dict(
                [
                    AddressAliases.STREET_ADDRESS.value,
                    AddressAliases.CITY.value,
                    AddressAliases.STATE.value,
                    AddressAliases.ZIP_CODE.value,
                ]
            )
            sql = _UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SQL[
                self._platform.config.platform_type
            ]
            sql = sql.format(
                full_ref_output_table=full_ref_output_table,
                street_address=address_columns.get(
                    AddressAliases.STREET_ADDRESS.value, ""
                ),
                city=address_columns.get(AddressAliases.CITY.value, ""),
                state=address_columns.get(AddressAliases.STATE.value, ""),
                zip_code=address_columns.get(AddressAliases.ZIP_CODE.value, ""),
            )
            self._database_client.execute(sql=sql)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error updating normalized_full_address."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def _update_current_hash(self, full_input_table: str) -> None:
        """Update the current hash in the reference table."""
        sql = ""
        params = []
        try:
            full_ref_output_table = self._table.get_table_name(full_input_table)
            logger.info(
                "Updating current hash in the reference table: %s",
                full_ref_output_table,
            )
            hashed_column_names = self._hash_input_columns()
            if self._platform.config.platform_type == PlatformType.BIGQUERY:
                hash_expression = (
                    f"CAST(FARM_FINGERPRINT({hashed_column_names}) AS STRING)"
                )
            else:
                hash_expression = f"HASH({hashed_column_names})"

            sql = f"""
            UPDATE {full_ref_output_table}
            SET {ClipOutputReferenceColumns.CURRENT_HASH.value} = {hash_expression}
            WHERE {ClipOutputReferenceColumns.CURRENT_HASH.value} = ''
            """.strip()
            # logger.info(sql)
            self._database_client.execute(sql=sql)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error updating current hash."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex

    def _update_clip_status_for_updated_records(self, full_input_table: str) -> None:
        """Update the clip status to UPDATED for records where previous_hash != current_hash"""
        try:
            # Update clip_status if previous_hash != current_hash
            full_ref_output_table = self._table.get_table_name(full_input_table)
            next_retry = datetime_to_int(day_offset=-5)
            sql = _UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SQL[
                self._platform.config.platform_type
            ].format(
                full_ref_output_table=full_ref_output_table,
            )
            params = [PropertyClipStatus.UPDATED.value, next_retry]
            self._database_client.execute(sql=sql, params=params)
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA,
                parameters={"name": full_input_table},
                message=(
                    f"Error updating status for changed current hash."
                    f"Table:{full_ref_output_table}, SQL: {sql}, Params: {params}"
                ),
                cause=ex,
            ) from ex


# ============ Private Schema Definition ============
# Delere all records from Reference output where PK is not loger in the Input table
_DELETE_STALE_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL = """
DELETE FROM {full_ref_output_table} AS ref
WHERE NOT EXISTS (
  SELECT 1
    FROM {full_input_table} AS input
   WHERE input.{pk} = ref.{pk}
)
""".strip()

_DELETE_STALE_OUTPUT_REF_RECORDS_SQL = {
    PlatformType.SNOWFLAKE: _DELETE_STALE_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _DELETE_STALE_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _DELETE_STALE_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
}

# Add new input records to output ref table
_INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SNOWFLAKE_SQL = """
INSERT INTO {{full_ref_output_table}}
({pk}, {{input_column_names}}, {{meta_column_names}})
SELECT
    cleaned.{pk},
    {{cleaned_input_columns}},
    '' as {normalized_full_address},
    '' as {previous_hash},
    '' as {current_hash},
    ? as {clip_status},
    '' as {message},
    '' as {message_details},
    ? as {next_retry_at},
    0 as {retry_attempts}
FROM (
    SELECT
        input.{pk},
        {{cleaned_input_expressions}}
    FROM {{full_input_table}} input
) AS cleaned
LEFT JOIN {{full_ref_output_table}} AS ref ON ref.{pk} = cleaned.{pk}
WHERE ref.{pk} IS NULL
""".strip().format(
    pk=ClipOutputReferenceColumns.REFERENCE_ID.value,
    normalized_full_address=ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value,
    previous_hash=ClipOutputReferenceColumns.PREVIOUS_HASH.value,
    current_hash=ClipOutputReferenceColumns.CURRENT_HASH.value,
    clip_status=ClipOutputReferenceColumns.CLIP_STATUS.value,
    message=ClipOutputReferenceColumns.MESSAGE.value,
    message_details=ClipOutputReferenceColumns.MESSAGE_DETAILS.value,
    next_retry_at=ClipOutputReferenceColumns.NEXT_RETRY_AT.value,
    retry_attempts=ClipOutputReferenceColumns.RETRY_ATTEMPTS.value,
)

_INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SQL = {
    PlatformType.SNOWFLAKE: _INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _INSERT_UNIQUE_RECORDS_TO_OUTPUT_REF_SNOWFLAKE_SQL,
}

# Update all records in output ref table from input table
# Set previous_hash to current_hash, current_hash to hash of property columns
# Set normalized_full_address to empty string (to be populated later
_UPDATE_ALL_OUTPUT_REF_SNOWFLAKE_SQL = """
UPDATE {{full_ref_output_table}} AS ref
SET
  {{set_clauses}},
  {normalized_full_address} = '',
  {previous_hash} = ref.{current_hash},
  {current_hash} = ''
FROM (
    SELECT
        input.{pk},
        {{cleaned_input_expressions}}
    FROM {{full_input_table}} AS input
) AS cleaned
WHERE ref.{pk} = cleaned.{pk}
""".strip().format(
    pk=ClipOutputReferenceColumns.REFERENCE_ID.value,
    normalized_full_address=ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value,
    previous_hash=ClipOutputReferenceColumns.PREVIOUS_HASH.value,
    current_hash=ClipOutputReferenceColumns.CURRENT_HASH.value,
)

_UPDATE_ALL_OUTPUT_REF_SQL = {
    PlatformType.SNOWFLAKE: _UPDATE_ALL_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_ALL_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_ALL_OUTPUT_REF_SNOWFLAKE_SQL,
}

# Update Clip status to UPDATED for updated input records
_UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SNOWFLAKE_SQL = """
UPDATE {full_ref_output_table}
SET clip_status = ?,
next_retry_at = ?, retry_attempts = 0
WHERE previous_hash != current_hash
""".strip()

_UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SQL = {
    PlatformType.SNOWFLAKE: _UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_STATUS_FOR_UPDATED_OUTPUT_REF_SNOWFLAKE_SQL,
}

# Update reference records to reflect new  Clip records that have been clipped
_UPDATE_STATUS_FOR_CLIPPED_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL = """
UPDATE {full_ref_output_table}
SET clip_status = ?,
    next_retry_at = ?,
    message = ?,
    message_details = ?,
WHERE reference_id IN (
    SELECT reference_id FROM {clip_output} WHERE clip_id IS NOT NULL
)
""".strip()

_UPDATE_STATUS_FOR_CLIPPED_OUTPUT_REF_RECORDS_SQL = {
    PlatformType.SNOWFLAKE: _UPDATE_STATUS_FOR_CLIPPED_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_STATUS_FOR_CLIPPED_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_STATUS_FOR_CLIPPED_OUTPUT_REF_RECORDS_SNOWFLAKE_SQL,
}

# Update normalized_full_address in the reference table
_UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SNOWFLAKE_SQL = """
UPDATE {{full_ref_output_table}}
SET {normalized_address} = LOWER(
    CASE
        WHEN COALESCE(TRIM({full_address}), '') != '' THEN {full_address}
        ELSE CONCAT(
            COALESCE({{street_address}}, ''), ' ',
            COALESCE({{city}}, ''), ' ',
            COALESCE({{state}}, ''), ' ',
            COALESCE({{zip_code}}, '')
        )
    END
)
WHERE {normalized_address} = ''
""".strip().format(
    normalized_address=ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value,
    full_address=ClipOutputReferenceColumns.FULL_ADDRESS.value,
)

_UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SQL = {
    PlatformType.SNOWFLAKE: _UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_NORMAILZED_FULL_ADDRESS_OUTPUT_REF_SNOWFLAKE_SQL,
}

_CLIP_COLUMN_VALIDATION_SNOWFLAKE_SQL = """
UPDATE {{full_ref_output_table}}
SET {clip_status} = ?,
    {message} = 'Required Clip data is missing. Must provide: (street_address AND zip_code) OR (street_address AND city AND state) OR (apn AND fips_code) OR (full_address) OR (latitude AND longitude)',
    {next_retry_at} = -1,
    {retry_attempts} = 0
WHERE NOT (
    (COALESCE(TRIM({normalized_address}), '') != '')
    OR
    (COALESCE(TRIM({apn}), '') != '' AND COALESCE(TRIM({fips_code}), '') != '')
    OR
    ({latitude} IS NOT NULL AND {latitude} > 0 AND {longitude} IS NOT NULL AND {longitude} > 0)
)
""".strip().format(
    clip_status=ClipOutputReferenceColumns.CLIP_STATUS.value,
    message=ClipOutputReferenceColumns.MESSAGE.value,
    next_retry_at=ClipOutputReferenceColumns.NEXT_RETRY_AT.value,
    retry_attempts=ClipOutputReferenceColumns.RETRY_ATTEMPTS.value,
    normalized_address=ClipOutputReferenceColumns.NORMALIZED_FULL_ADDRESS.value,
    apn=AddressAliases.APN.value,
    fips_code=AddressAliases.FIPS_CODE.value,
    latitude=AddressAliases.LATITUDE.value,
    longitude=AddressAliases.LONGITUDE.value,
)

_CLIP_COLUMN_VALIDATION_SQL = {
    PlatformType.SNOWFLAKE: _CLIP_COLUMN_VALIDATION_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _CLIP_COLUMN_VALIDATION_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _CLIP_COLUMN_VALIDATION_SNOWFLAKE_SQL,
}

# Update reference records to reflect new  Clip records that have been clipped
_UPDATE_WITH_CLIPPED_RECORDS_SNOWFLAKE_SQL = """
UPDATE {ref_output_table}
SET clip_status = ?,
    next_retry_at = -1,
    message = '',
    message_details = ''
WHERE reference_id IN (
    SELECT reference_id FROM {clip_output} WHERE clip_id IS NOT NULL
)
""".strip()

_UPDATE_WITH_CLIPPED_RECORDS = {
    PlatformType.SNOWFLAKE: _UPDATE_WITH_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_WITH_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_WITH_CLIPPED_RECORDS_SNOWFLAKE_SQL,
}

# Update reference records to reflect new  Clip records that have NOT been clipped
_UPDATE_WITH_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL = """
UPDATE {ref_output_table}
SET clip_status = ?,
    retry_attempts = retry_attempts + 1,
    next_retry_at = CASE
        WHEN retry_attempts + 1 >= ? THEN -1
        ELSE ?
    END
WHERE reference_id IN (
    SELECT reference_id FROM {clip_output} WHERE clip_id IS NULL
)
""".strip()

_UPDATE_WITH_NOT_CLIPPED_RECORDS = {
    PlatformType.SNOWFLAKE: _UPDATE_WITH_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: _UPDATE_WITH_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: _UPDATE_WITH_NOT_CLIPPED_RECORDS_SNOWFLAKE_SQL,
}

__VALIDATE_INPUT_DATA_COMBINATIONS_SNOWFLAKE_SQL = """
UPDATE {{full_ref_output_table}}
SET clip_status = ?,
    message = 'Required Clip data is missing. Must provide: (street_address AND zip_code) OR (street_address AND city AND state) OR (full_address)',
    next_retry_at = -1,
    retry_attempts = 0
WHERE NOT (
    (COALESCE(TRIM({street_address}), '') != '' AND COALESCE(TRIM({zip_code}), '') != '')
    OR
    (COALESCE(TRIM({street_address}), '') != '' AND COALESCE(TRIM({city}), '') != '' AND COALESCE(TRIM({state}), '') != '')
    OR
    (COALESCE(TRIM({full_address}), '') != '')
)
""".strip().format(
    street_address=AddressAliases.STREET_ADDRESS.value,
    zip_code=AddressAliases.ZIP_CODE.value,
    city=AddressAliases.CITY.value,
    state=AddressAliases.STATE.value,
    full_address=AddressAliases.FULL_ADDRESS.value,
)

_VALIDATE_INPUT_DATA_COMBINATIONS_SQL = {
    PlatformType.SNOWFLAKE: __VALIDATE_INPUT_DATA_COMBINATIONS_SNOWFLAKE_SQL,
    PlatformType.DATABRICKS: __VALIDATE_INPUT_DATA_COMBINATIONS_SNOWFLAKE_SQL,
    PlatformType.BIGQUERY: __VALIDATE_INPUT_DATA_COMBINATIONS_SNOWFLAKE_SQL,
}
