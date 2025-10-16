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
"""Database Clip Client."""

import json
from logging import getLogger
from typing import Optional, Tuple

from pandas import DataFrame, to_datetime

from ...core.clgxtyping import AppSchemaID, PlatformType
from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from ...core.platform import Platform
from . import typing as clip_typing
from .private.clip_config import ClipConfig
from .private.clip_job import ClipJob
from .private.clip_job import Columns as ClipJobColumns
from .private.locale_clip_client import LocaleClipClient

logger = getLogger(__name__)


class ClipClient:
    """Database Clip Client"""

    def __init__(self, platform: Platform):
        """Initialize the DfClipClient with a DigitalGatewayClient.

        Args:
            digital_gateway_client (DigitalGatewayClient): Digital Gateway Client instance.
        """
        self._platform = platform
        platform.user_context.app_id = "clip"
        # Clip Client - Make sure this the last initialization step
        self._clip_client = LocaleClipClient(platform)
        self._app_config_table = self._clip_client.app_config_table
        self._clip_config_table = self._clip_client.clip_config_table
        self._clip_job_table = self._clip_client.clip_job_table
        self._clip_input_table = self._clip_client.clip_input_table
        self._clip_output_table = self._clip_client.clip_output_table
        self._clip_output_ref_table = self._clip_client.clip_output_ref_table
        self._app_config = self._clip_client.app_config

    # ================= Database related Clip functions
    def get_input_record_count(self, input_table_name: str) -> int:
        """Get the record count for the Clip input table.

        Args:
            input_table_name (str): Input table name for the Clip Lookup job.

        Returns:
            int: Record count for the Clip input table.
        """
        return self._clip_input_table.table.row_counts(input_table_name)

    def get_input_tables_summary(self) -> DataFrame:
        """
        Fetch a summary clip metrics of all Clip input tables.
        DataFrame includes:
            - Input Table Name
            - Total Records
            - Total CLIP Records
            - Last CLIP Run Records
            - Last CLIP Run Status
            - Last CLIP Run Data

        Returns:
            DataFrame: DataFrame containing summary information for all Clip input tables
        """
        # Row counts for all Clip Input tables
        # table_df = [clip_typing.INPUT_TABLE_NAME, clip_typing.TOTAL_RECORDS]
        row_counts_for_tables = self._clip_input_table.table.row_counts_for_tables()
        tables_df = DataFrame(
            [
                {
                    clip_typing.INPUT_TABLE_NAME: table_name,
                    clip_typing.TOTAL_RECORDS: row_count,
                }
                for table_name, row_count in row_counts_for_tables.items()
            ]
        )
        # Add another column for Output
        # table_df.[clip_typing.CLIP_OUTPUT_TABLE] = [clip_output_table_name, clip_output_row_counts]
        tables_df[clip_typing.CLIP_OUTPUT_TABLE] = tables_df[
            clip_typing.INPUT_TABLE_NAME
        ]
        # Get row counts from CLIP_OUTPUT.{table_name}_TEMP_DEDUP tables
        temp_dedup_counts = {}
        for table_name in tables_df[clip_typing.INPUT_TABLE_NAME]:
            temp_table_name = f"{table_name}_TEMP_DEDUP"
            full_temp_table_name = self._clip_output_table.table.get_table_name(
                temp_table_name
            )
            try:
                temp_dedup_counts[table_name] = (
                    self._clip_output_table.table.row_counts(full_temp_table_name)
                )
            except Exception:
                temp_dedup_counts[table_name] = 0

        if temp_dedup_counts:
            clip_output_df = DataFrame(
                [
                    {
                        clip_typing.CLIP_OUTPUT_TABLE: table_name,
                        clip_typing.TOTAL_CLIP_RECORDS: row_count,
                    }
                    for table_name, row_count in temp_dedup_counts.items()
                ]
            )

            tables_df = tables_df.merge(
                clip_output_df,
                on=clip_typing.CLIP_OUTPUT_TABLE,
                how="left",
                validate="1:1",
            )
        else:
            tables_df[clip_typing.TOTAL_CLIP_RECORDS] = 0

        # Job summary for each Input table
        input_tables = tables_df[clip_typing.INPUT_TABLE_NAME].tolist()
        # clip_tables = tables_df[clip_typing.CLIP_OUTPUT_TABLE].tolist()
        jobs_data = self._clip_job_table.get_job_summary(input_tables)

        tables_df = tables_df.merge(
            jobs_data, on=clip_typing.INPUT_TABLE_NAME, how="left", validate="1:1"
        )
        tables_df = tables_df.drop(columns=[clip_typing.CLIP_OUTPUT_TABLE])

        date_format = self._platform.config.locale.date_format

        tables_df[clip_typing.LAST_CLIP_RUN_DATE] = to_datetime(
            tables_df[clip_typing.LAST_CLIP_RUN_DATE],
            format="%Y%m%d%H%M%S",
            errors="coerce",
        )

        tables_df[clip_typing.LAST_CLIP_RUN_DATE] = tables_df[
            clip_typing.LAST_CLIP_RUN_DATE
        ].dt.strftime(date_format)

        # Should we move it somewhere else?
        status_map = {
            clip_typing.RunStatus.RUNNING.value: "In Progress",
            clip_typing.RunStatus.SUCCEEDED.value: "Completed",
            clip_typing.RunStatus.DUPLICATED_PK.value: "Failed",
            clip_typing.RunStatus.THRESHOLD_EXCEEDED.value: "Failed",
            clip_typing.RunStatus.FAILED.value: "Failed",
            clip_typing.RunStatus.UNKNOWN.value: "Initiated",
        }

        tables_df[clip_typing.LAST_CLIP_RUN_STATUS] = (
            tables_df[clip_typing.LAST_CLIP_RUN_STATUS]
            .str.lower()
            .map(status_map)
            .fillna("Not Started")
        )

        # Finale Dataframe schema
        #  [clip_typing.INPUT_TABLE_NAME, clip_typing.TOTAL_RECORDS, clip_typing.TOTAL_CLIP_RECORDS,
        # clip_typing.LAST_CLIP_RUN_STATUS, clip_typing.LAST_CLIP_RUN_DATE, clip_typing.LAST_CLIP_RUN_RECORDS]
        return DataFrame(tables_df)

    def get_input_jobs_list(
        self, input_table_name: str
    ) -> list[tuple[clip_typing.ClipLookupStatus, clip_typing.ClipMetrics]]:
        """Get a list of jobs asociated to this input table.

        Args:
            input_table_name (str): Input table name for the Clip Lookup job.

        Returns
            list[tuple[ClipLookupStatus, ClipMetrics]]: List of ClipLookupStatus
                and ClipMetrics tuples for the input table.
        """

        quotation = self._platform.database_client.config.string_quotation
        jobs = self._clip_job_table.table.select(
            where_clause=f"{ClipJobColumns.INPUT_TABLE}={quotation}{input_table_name}{quotation}",
            order_by=f"{ClipJobColumns.COMPLETED_AT} desc",
        )
        clip_jobs = []
        if isinstance(jobs, list):
            clip_jobs = jobs
        elif jobs:
            clip_jobs.append(jobs)

        def _map(job):
            return (
                clip_typing.ClipLookupStatus(
                    job_id=job.job_id,
                    status=clip_typing.RunStatus(job.status),
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                    elapsed_time_in_seconds=job.elapsed_time_in_seconds,
                    exception=None,
                    exception_df=None,
                    input_metrics=job.clip_metrics.input_metrics,
                ),
                job.clip_metrics,
            )

        return [_map(job) for job in clip_jobs]

    def get_input_job_count(self, input_table_name: str) -> int:
        """Get the job count for the Clip input table.

        Args:
            platform (Platform): Platform object
            input_table_name (str): Input table name for the Clip Lookup job.

        Returns:
            int: Job count for the Clip input table.
        """
        quotation = self._platform.database_client.config.string_quotation
        conditions = (
            f"{ClipJobColumns.INPUT_TABLE}={quotation}{input_table_name}{quotation}"
        )
        return self._clip_job_table.table.get_row_counts(conditions=conditions)

    def get_clip_input_table_data(self, table: str) -> DataFrame:
        """Get the Clip input table data.
        This function is used to get the data from the Clip input table.

        Args:
            platform (Platform): Platform object
            table (str): Input table name

        Returns:
            DataFrame: DataFrame containing the Clip input table data
        """
        input_db, input_schema = self._platform.get_schema(AppSchemaID.CLIP_INPUT)

        full_table_name = self._platform.database_client.full_table_name(
            input_db, input_schema, table
        )

        return self._clip_input_table.table.table_to_pandas(
            table_name=full_table_name, limit=20
        )

    def get_clip_job(self, job_id: str) -> ClipJob | None:
        """Get the Clip job by job ID.

        Args:
            job_id (str): Job ID for the Clip Lookup job.

        Returns:
            ClipJob: ClipJob object for the given job ID.
        """
        jobs = self._clip_job_table.table.get(primary_key_values=job_id)
        return jobs[0] if jobs else None

    # def get_clip_job_results(self, input_table_name: str, job_id: str) -> ClipJob:
    # Obsolete, please use get_clip_job instead

    # ========== Metrics Functions ==========
    def get_job_metrics(self, job_id: str) -> clip_typing.ClipMetrics:
        """Get job metrics
        This function is used to get the metrics for the Clip Lookup service.

        Args:
            platform (Platform): Platform object
            job_id (str): Job ID for the Clip Lookup job.

        Returns:
            ClipMetrics: Metrics for the Clip Lookup service.
        """
        job = self.get_clip_job(job_id)
        return (
            job.clip_metrics if job and job.clip_metrics else clip_typing.ClipMetrics()
        )

    def get_input_metrics(self, input_table: str) -> clip_typing.ClipMetrics:
        """Get metrics for the whole input table.
        This function is used to get the metrics for the Clip Lookup service without specifying a job ID.

        Args:
            input_table (str): Input table name for the Clip Lookup.

        Returns:
            ClipMetrics: Metrics for the Clip Lookup service.
        """
        return self._clip_output_table.get_clip_metrics(table_name=input_table)

    def get_digital_gateway_credential(self) -> Tuple[str, str]:
        """Get the Digital Gateway credential for the Clip Lookup service.
        This function is used to get the credential for the Digital Gateway service.

        Args:
            platform (Platform): Platform object

        Returns:
            Tuple[str,str]: Tuple containing the credential username and password.
        """
        return self._platform.secret_client.get_digital_gateway_credential()

    def save_digital_gateway_credential(self, username: str, password: str) -> None:
        """Save the Digital Gateway credential for the Clip Lookup service.
        This function is used to save the credential for the Digital Gateway service.

        Args:
            platform (Platform): Platform object
            username (str): Username for the Digital Gateway service
            password (str): Password for the Digital Gateway service
        """
        if username and password:
            response = self._platform.set_digital_gatewaycredential(username, password)
            status = response.success
            if status:
                self._platform.secret_client.save_digital_gateway_credential(
                    username, password
                )

    # ========== Input Functions ==========
    def get_clip_input_tables(self) -> list[str]:
        """Call this from application to get the Clip input tables.
        If there are more than 1 tables, prompt the user to select one.
        If there none, prompt user to create new in[ut table.
        Users must populate the input tables with data before attempt to run the Clip Lookup.

        Args:
            platform (Platform): Platform instance

        Returns:
            list[str]: List of Clip input table names
        """
        return self._clip_input_table.table.get_tables()

    def create_clip_input_table(self, table: str) -> None:
        """Call this funtion to create new Clip input table.
        Users must populate the input tables with data before attempt to run the Clip Lookup.

        Args:
            platform (Platform): Platform instance
            table (str): Input table name
        """
        logger.info("Creating Clip input table: %s", table)
        self._clip_input_table.table.create(table_name=table)

    def _create_clip_internal_tables(self, input_table: str) -> None:
        """Create internal tables for the Clip Lookup process.

        Args:
            input_table (str): The name of the Clip input table.
        """
        logger.info("Creating internal tables for Clip input table: %s", input_table)
        self._app_config_table.init_job()
        self._clip_config_table.table.init_job(input_table=input_table)
        self._clip_job_table.init_job(input_table=input_table)
        self._clip_output_table.init_job(input_table=input_table)
        self._clip_output_ref_table.init_job(input_table=input_table)

    # ========== Clip Config Functions ==========
    def get_clip_lookup_config(self, input_table: str) -> ClipConfig:
        """Call this function to get the Clip Lookup configuration.
        This function will return the configuration for the lookup.

        Args:
            input_table (str): Input table name without database & schema
        Returns:
            ClipConfig: ClipConfig object for the given input table.
        """
        return self._clip_config_table.table.get(input_table)

    # =============== Clip functions

    def clip(
        self,
        input_table: str,
        limit: int = 0,
        stop_after_submit: bool = False,
        clip_config: Optional[ClipConfig] = None,
        event_callback=None,
    ) -> None:
        """Clip the input table based on the provided configuration and status.

        Args:
            input_table (str): The name of the input table to clip.
            limit (int, optional): The maximum number of rows to process. Defaults to 0 (no limit).
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            clip_config (ClipConfig, optional): The ClipConfig object. If None, the configuration will be fetched from the database.
            event_callback (_type_, optional): _description_. Defaults to None.
        """
        if (
            self._platform.config.platform_type == PlatformType.SNOWFLAKE
            and not self._platform.config.has_access_to_external_integration
        ):
            self.__usp_clip(
                input_table=input_table,
                limit=limit,
                stop_after_submit=stop_after_submit,
            )
        else:
            self.__clip(
                input_table=input_table,
                limit=limit,
                event_callback=event_callback,
                stop_after_submit=stop_after_submit,
            )

    def __usp_clip(
        self,
        input_table: str,
        limit: int = 0,
        stop_after_submit: bool = False,
        clip_config: Optional[ClipConfig] = None,
    ) -> None:
        """Clip the input table using the stored procedure USP_CLIP_LOOKUP.
        For snowflake without external integration access.

        Args:
            input_table (str): The name of the input table to clip.
            limit (int, optional): The maximum number of rows to process. Defaults to 0 (no limit).
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            clip_config (ClipConfig, optional): The ClipConfig object. If None, the configuration will be fetched from the database.
        """
        _, _, input_table_only = self._platform.database_client.parse_table(input_table)
        self._platform.database_client.call_proc(
            "USP_CLIP_LOOKUP", input_table_only, limit, stop_after_submit
        )

    def __clip(
        self,
        input_table: str,
        limit: int = 0,
        stop_after_submit: bool = False,
        clip_config: Optional[ClipConfig] = None,
        event_callback=None,
    ) -> None:
        """Clip the input DataFrame based on the provided configuration and status.

        Args:
            input_table (str): Input table name
            limit (int, optional): Maximum number of rows to process. Defaults to 0 (no limit).
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            clip_config (ClipConfig, optional): ClipConfig object. If None, the configuration will be fetched from the database.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """
        logger.info("Starting Clip Lookup for table: %s, Limit: %d", input_table, limit)
        self._create_clip_internal_tables(input_table=input_table)

        _, _, input_table_only = self._platform.database_client.parse_table(input_table)
        input_row_counts = 0
        try:
            clip_job = self._clip_job_table.lock(input_table=input_table_only)
            if clip_job.status == clip_typing.RunStatus.RUNNING:
                if not clip_config:
                    clip_config = self._clip_config_table.table.get(input_table_only)
                input_query_sql = ""
                clip_input_mappings = {}
                if clip_job.status == clip_typing.RunStatus.RUNNING:
                    if clip_job.step == clip_typing.ClipLookupAction.INITIALIZE:
                        self._clip_output_table.create_temp_tables(clip_job.input_table)
                    if clip_job.step < clip_typing.ClipLookupAction.SUBMIT_JOB:
                        self._clip_input_table.validate_schema(clip_job.input_table)
                        self._prepare_input_ref_records(clip_job, limit)
                        invalid_row_counts_before, invalid_row_counts_after = (
                            self._clip_output_ref_table.validate_required_clip_data(
                                clip_job.input_table
                            )
                        )
                        input_row_counts, input_query_sql, clip_input_mappings = (
                            self._clip_output_ref_table.collect_clip_input_records(
                                clip_job.input_table, limit
                            )
                        )
                        self._update_input_metrics(
                            clip_job,
                            input_row_counts=input_row_counts,
                            invalid_row_counts_before=invalid_row_counts_before,
                            invalid_row_counts_after=invalid_row_counts_after,
                        )
                        self._clip_job_table.update(clip_job)
                    if input_row_counts == 0:
                        clip_job.status = clip_typing.RunStatus.SUCCEEDED
                        clip_job.step = clip_typing.ClipLookupAction.CLEANUP
                        clip_job.message = "No new or updated records to process."
                        logger.info(
                            "No new or updated records to process for table: %s",
                            input_table,
                        )
                    else:
                        self._clip_client.lookup(
                            clip_config=clip_config,
                            clip_job=clip_job,
                            row_counts=input_row_counts,
                            input_query=input_query_sql,
                            clip_input_mappings=clip_input_mappings,
                            stop_after_submit=stop_after_submit,
                        )
        except ClgxException as e:
            clip_job.status = clip_typing.RunStatus.FAILED
            clip_job.message = e.external_message
            clip_job.message_details = str(e)
            logger.error("Clip Lookup failed with exception: %s", str(e))

        except Exception as e:
            exception = ClgxException(
                error=CommonErrorCodes.CLIP_APP_CONFIG,
                message="Unexpected error during Clip Lookup process.",
                cause=e,
            )
            clip_job.status = clip_typing.RunStatus.FAILED
            clip_job.message = exception.external_message
            clip_job.message_details = str(exception)
            logger.error(
                "Clip Lookup failed with unexpected exception: %s", str(exception)
            )

        finally:
            self._finallize(clip_config, clip_job)
            self._clip_job_table.release(clip_job)

    # ========== Private functions ==========

    def _update_input_metrics(
        self,
        clip_job: ClipJob,
        input_row_counts: int,
        invalid_row_counts_before: int,
        invalid_row_counts_after: int,
    ) -> None:
        """Update the metrics for the Clip Lookup process.
        This function is used to update the metrics for the Clip Lookup process.

        Args:
            platform (Platform): Platform object
            clip_job (ClipJob): The ClipJob instance.
            input_row_counts (int): Total number of input records
            invalid_row_counts_before (int): Number of invalid records before processing
            invalid_row_counts_after (int): Number of invalid records after processing
        """
        # Update metrics
        clip_job.clip_metrics.input_metrics.invalid_counts = (
            invalid_row_counts_after - invalid_row_counts_before
        )
        clip_job.clip_metrics.input_metrics.total_input_counts = (
            input_row_counts + clip_job.clip_metrics.input_metrics.invalid_counts
        )
        clip_job.clip_metrics.input_metrics.invalid_percentage = (
            (
                clip_job.clip_metrics.input_metrics.invalid_counts
                / input_row_counts
                * 100
            )
            if input_row_counts > 0
            else 0.0
        )
        self._clip_job_table.table.update(clip_job)

    def _finallize(self, config: ClipConfig, clip_job: ClipJob) -> None:
        """Finalize the Clip Lookup process.
        This function is used to finalize the Clip Lookup process.

        Args:
            platform (Platform): Platform object
        """
        if clip_job.status == clip_typing.RunStatus.RUNNING:
            try:
                self._clip_output_table.update_clip_metrics(clip_job)
                ref_input_column_names = self._clip_output_ref_table.input_colmn_names
                full_reference_table = self._clip_output_ref_table.table.get_table_name(
                    clip_job.input_table
                )
                _, tmp_full_table_name = self._clip_output_table.get_temp_tables(
                    clip_job.input_table
                )
                self._clip_output_table.consolidate_clip_output_table(
                    clip_job.input_table, full_reference_table, ref_input_column_names
                )
                _, full_clip_output_temp_table = (
                    self._clip_output_table.get_temp_tables(clip_job.input_table)
                )
                clip_job.clip_metrics.clip_summary_metric = (
                    self._clip_output_table.table.aggregate_clip_metric(
                        table_name=full_clip_output_temp_table
                    )
                )
                self._clip_output_ref_table.update_reference_table(
                    clip_job.input_table,
                    tmp_full_table_name,
                    self._app_config.next_retry_interval,
                    self._app_config.max_retry_attempts,
                )
                if clip_job.step == clip_typing.ClipLookupAction.SAVE_RESULTS:
                    clip_job.status = clip_typing.RunStatus.SUCCEEDED
                    clip_job.step = clip_typing.ClipLookupAction.CLEANUP
                    clip_job.message = "Clip Lookup completed successfully."
            except ClgxException as e:
                clip_job.status = clip_typing.RunStatus.FAILED
                clip_job.message = e.external_message
                clip_job.message_details = str(e)
            except Exception as e:
                exception = ClgxException(
                    error=CommonErrorCodes.CLIP_APP_CONFIG, cause=e
                )
                clip_job.status = clip_typing.RunStatus.FAILED
                clip_job.message = exception.external_message
                clip_job.message_details = str(exception)

    def _prepare_input_ref_records(self, clip_job: ClipJob, limit: int = 0) -> None:
        """Prepare the reference records for the Clip Lookup process.

        Args:
            clip_job (ClipJob): The ClipJob instance.
            limit (int, optional): The maximum number of rows to process. Defaults to 0 (no limit).
        """
        full_input_table_name = self._clip_input_table.table.get_table_name(
            clip_job.input_table
        )
        self._clip_output_ref_table.delete_orphan_input_records(
            full_input_table=full_input_table_name
        )
        self._clip_output_ref_table.update_input_changed_records(
            full_input_table=full_input_table_name
        )
        self._clip_output_ref_table.add_new_input_records(
            full_input_table=full_input_table_name, limit=limit
        )
        self._clip_output_ref_table.update_normalized_full_address(
            full_input_table=full_input_table_name
        )


# =========== Database Mapping
