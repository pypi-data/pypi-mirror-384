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
"""US Clip Client"""
from __future__ import annotations

import logging
from typing import Tuple

import pandas as pd
from pandas._typing import DtypeArg

from .....core.clgxtyping import FileFormat
from .....core.error_codes import CommonErrorCodes
from .....core.exception import ClgxException
from .....core.interfaces.database_types import get_pandas_dtype_from_enum
from .....core.platform import Platform
from .....core.utils.misc import datetime_to_int
from ....database.dmz_export import DmzExport, get_file_extension
from ....database.dmz_import import DmzImport
from ...typing import (
    CLIP_COLUMNS_GROUP,
    CLIP_STEP_LOG_PREFIX,
    PRIMARY_KEY_GROUP,
    STORAGE_ID,
    STORAGE_INPUT_SUFFIX,
    STORAGE_OUTPUT_SUFFIX,
    ClipLookupAction,
    RunStatus,
)
from ..app_config import AppConfig
from ..clip_config import ClipConfig
from ..clip_job import ClipJob, ClipJobStatus, ClipJobTable
from ..locale_output import ClipOutputTable
from . import status as status_module
from . import submit as submit_module

logger = logging.getLogger(__name__)


class ClipClientUS:
    """Clip Client"""

    def __init__(
        self,
        platform: Platform,
        app_config: AppConfig,
        clip_job_table: ClipJobTable,
        clip_output_table: ClipOutputTable,
        dmz_export: DmzExport,
        dmz_import: DmzImport,
    ):
        """Initialize the DfClipClient with a DigitalGatewayClient.

        Args:
            platform (Platform): Platform object
            app_config (AppConfig): App configuration instance
            clip_job_table (ClipJobTable): Clip job table instance
            clip_output_table (ClipJobTable): Clip output table instance
            dmz_export (DmzExport): DMZ Export client instance
            dmz_import (DmzImport): DMZ Import client instance
        """
        self._platform = platform
        self._database_client = platform.database_client
        self._app_config = app_config
        self._clip_job_table = clip_job_table
        self._clip_output_table = clip_output_table
        self._dmz_export = dmz_export
        self._dmz_import = dmz_import
        self._column_name_mapping, self._panda_data_types = (
            self._get_clip_result_mapping()
        )
        self._file_extension = get_file_extension(app_config.file_format)

    def lookup(
        self,
        clip_config: ClipConfig,
        clip_job: ClipJob,
        row_counts: int,
        input_query: str,
        clip_input_mappings: dict[str, str],
        stop_after_submit: bool = False,
        event_callback=None,
    ) -> None:
        """Execute the clip lookup.

        mapping = {
            "clip_id: "clip_clip"
        }
        Args:
            clip_config (ClipConfig): lip configuration instance
            clip_job (ClipJob): Clip job instance
            row_counts (int): Total number of records to process
            input_query (str): SQL query string to fetch input data
            clip_input_mappings (dict): Mapping of Clip attributes to input column names
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            upload_format (FileFormat, optional): Format of the uploaded file. Defaults to FileFormat.CSV.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """
        logger.info(
            "Calling Clip lookup. Job ID:%s, Step:%s,%s, Input:%s.",
            clip_job.job_id,
            clip_job.step.name,
            clip_job.step.value,
            clip_config.input_table,
        )

        if (
            clip_job.status == RunStatus.RUNNING
            and clip_job.step < ClipLookupAction.UPLOAD_INPUT_DATA
        ):
            self._upload(
                clip_config=clip_config,
                clip_job=clip_job,
                row_counts=row_counts,
                input_query=input_query,
                event_callback=event_callback,
            )

        if (
            clip_job.status == RunStatus.RUNNING
            and clip_job.step < ClipLookupAction.SUBMIT_JOB
        ):
            self._submit(
                clip_config=clip_config,
                clip_job=clip_job,
                clip_input_mappings=clip_input_mappings,
                event_callback=event_callback,
            )

        if (
            clip_job.status == RunStatus.RUNNING
            and clip_job.step <= ClipLookupAction.POLL_JOB
        ):
            self._get_job_status(
                clip_config=clip_config,
                clip_job=clip_job,
                event_callback=event_callback,
                stop_after_submit=stop_after_submit,
            )

        if (
            clip_job.clip_job_status == ClipJobStatus.COMPLETED
            and clip_job.status == RunStatus.RUNNING
            and clip_job.step < ClipLookupAction.SAVE_RESULTS
        ):
            self._download(
                clip_config=clip_config,
                clip_job=clip_job,
                event_callback=event_callback,
            )

    # =========================Private Functions=========================

    def _get_clip_result_mapping(self) -> Tuple[dict[str, str], DtypeArg]:
        """Validate the clip input mappings.

        Returns:
            Tuple[dict[str, str], dict[str,str]]: A tuple containing:
                - A dictionary mapping Clip response column aliases to actual column names.
                - A dictionary mapping column aliases to their corresponding pandas data types.
        """
        groups = self._clip_output_table.table.get_columns_by_group(
            [PRIMARY_KEY_GROUP, CLIP_COLUMNS_GROUP]
        )
        columns = groups.get(PRIMARY_KEY_GROUP, []) + groups.get(CLIP_COLUMNS_GROUP, [])
        panda_data_types: DtypeArg = {}
        column_name_mapping = {}
        for col in columns:
            panda_data_types[col.alias] = get_pandas_dtype_from_enum(col.data_type)
            column_name_mapping[col.alias] = col.name
        return column_name_mapping, panda_data_types

    def _upload(
        self,
        clip_config: ClipConfig,
        clip_job: ClipJob,
        row_counts: int,
        input_query: str,
        event_callback=None,
    ) -> None:
        """Uploads input data to cloud storage via DMZ signed URLs.

        Args:
            clip_config (ClipConfig): The configuration for the clip lookup.
            clip_job (ClipJob): The clip job instance.
            row_counts (int): Total number of records to process
            input_query (str): The SQL query to retrieve the input data.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """
        logger.info(
            "%s %s - Uploading input data to cloud storage via DMZ signed URLs. Input:%s",
            CLIP_STEP_LOG_PREFIX,
            clip_job.step.value,
            clip_config.input_table,
        )
        try:
            upload_format = self._app_config.file_format or FileFormat.CSV
            file_upload_response = self._dmz_export.export_data(
                storage_id=STORAGE_ID,
                base_path=STORAGE_INPUT_SUFFIX,
                row_counts=row_counts,
                query_sql=input_query,
                upload_format=upload_format,
                max_records_per_url=10000,
            )
            clip_job.set_storage_attributes(
                url_prefix=file_upload_response.url_prefix,
                storage_prefix=file_upload_response.storage_prefix,
            )
            clip_job.step = ClipLookupAction.UPLOAD_INPUT_DATA
            self._clip_job_table.update(
                clip_job=clip_job, event_callback=event_callback
            )
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_UPLOAD_CLIP_DATA,
                parameters={"name": clip_config.input_table},
                message=(
                    f"Failed to upload input records. Job: {clip_job.job_id}, Input:{clip_config.input_table}. "
                ),
                cause=ex,
            ) from ex

    def _submit(
        self,
        clip_config: ClipConfig,
        clip_job: ClipJob,
        clip_input_mappings: dict[str, str],
        event_callback=None,
    ) -> None:
        """Submits the clip job to the Clip service.
        Args:
            clip_config (ClipConfig): The configuration for the clip lookup.
            clip_job (ClipJob): The clip job instance.
            clip_input_mappings (dict[str, str]): A mapping of input column names to their corresponding storage paths.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """
        logger.info(
            "%s %s - Submit clip job. Input:%s",
            CLIP_STEP_LOG_PREFIX,
            clip_job.step.value,
            clip_config.input_table,
        )
        try:
            submit_module.execute(
                platform=self._platform,
                app_config=self._app_config,
                clip_config=clip_config,
                clip_job=clip_job,
                input_bucket_location=f"{clip_job.storage_input_url}/*.{self._file_extension}",
                output_bucket_location=clip_job.storage_output_url,
                clip_input_mappings=clip_input_mappings,
            )
            clip_job.step = ClipLookupAction.SUBMIT_JOB
            self._clip_job_table.update(
                clip_job=clip_job, event_callback=event_callback
            )
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_CALL_CLIP_API,
                parameters={"name": clip_config.input_table},
                message=f"Failed to submit clip job:{clip_job.job_id}. Input:{clip_config.input_table}",
                cause=ex,
            ) from ex

    def _get_job_status(
        self,
        clip_config: ClipConfig,
        clip_job: ClipJob,
        stop_after_submit: bool = False,
        event_callback=None,
    ) -> None:
        """Monitors the status of the submitted clip job.
        Args:
            clip_config (ClipConfig): The configuration for the clip lookup.
            clip_job (ClipJob): The clip job instance.
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """

        logger.info(
            "%s %s - Monitor clip lookup job status. Input:%s",
            CLIP_STEP_LOG_PREFIX,
            clip_job.step.value,
            clip_config.input_table,
        )
        try:
            status_module.execute(
                platform=self._platform,
                clip_job=clip_job,
                clip_job_table=self._clip_job_table,
                stop_after_submit=stop_after_submit,
            )
            clip_job.step = ClipLookupAction.POLL_JOB
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_CHECK_CLIP_JOB,
                parameters={"name": clip_config.input_table},
                message=f"Failed to monitor clip job status:{clip_job.job_id}. Input:{clip_config.input_table}",
                cause=ex,
            ) from ex

    def save_clip_results(self, dataframe: pd.DataFrame, clip_job) -> None:
        """Convert the clip response data frame based on the response mapping.

        Args:
            dataframe (pd.DataFrame): The original clip response data frame.
            clip_job (ClipJob): The clip job instance.
        """
        try:
            dedup_table_name, _ = self._clip_output_table.get_temp_tables(
                clip_job.input_table
            )
            self._database_client.append_data(
                table=dedup_table_name, dataframe=dataframe
            )
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": clip_job.job_id},
                message=f"Failed to save clip results to table:{dedup_table_name}. Job ID:{clip_job.job_id}",
                cause=ex,
            ) from ex

    def _download(
        self,
        clip_config: ClipConfig,
        clip_job: ClipJob,
        event_callback=None,
    ) -> None:
        """Uploads input data to cloud storage via DMZ signed URLs.

        Args:
            clip_config (ClipConfig): The configuration for the clip lookup.
            clip_job (ClipJob): The clip job instance.
            input_query (str): The SQL query to retrieve the input data.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """

        logger.info(
            "%s %s - Retrieve clip lookup results. Input:%s",
            CLIP_STEP_LOG_PREFIX,
            clip_job.step.value,
            clip_config.input_table,
        )
        try:
            self._dmz_import.import_data(
                storage_id=STORAGE_ID,
                base_path=clip_job.storage_download_path,
                data_types=self._panda_data_types,
                column_name_mapping=self._column_name_mapping,
                save_result_callback=lambda dataframe: self.save_clip_results(
                    dataframe, clip_job
                ),
                download_format=FileFormat.CSV,
            )
            clip_job.step = ClipLookupAction.SAVE_RESULTS
            self._clip_job_table.update(
                clip_job=clip_job, event_callback=event_callback
            )
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.CLIP_FAILED_TO_SAVE_CLIP_RESULTS,
                parameters={"name": clip_config.input_table},
                message=f"Failed to download results clip job:{clip_job.job_id}. Input:{clip_config.input_table}",
                cause=ex,
            ) from ex
