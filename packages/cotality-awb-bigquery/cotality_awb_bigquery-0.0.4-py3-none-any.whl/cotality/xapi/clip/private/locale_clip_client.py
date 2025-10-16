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
"""Clip Client Interface."""
from __future__ import annotations

from ....core.clgxtyping import AppSchemaID, Country, CSVConfig
from ....core.error_codes import CommonErrorCodes
from ....core.exception import ClgxException
from ....core.platform import Platform
from ...database.dmz_export import DmzExport
from ...database.dmz_import import DmzImport
from ...dmz.client import DmzClient
from .app_config import AppConfig, AppConfigTable
from .clip_config import ClipConfig, ClipConfigTable
from .clip_job import ClipJob, ClipJobTable
from .clip_us.clip_client import ClipClientUS
from .locale_input import ClipInputTable
from .locale_output import ClipOutputTable
from .locale_output_ref import ClipOutputReferenceTable


class LocaleClipClient:
    """Base class for Clip Client Interface"""

    def __init__(self, platform: Platform):
        """Initialize the ClipClientInterface instance.

        Args:
            platform (Platform): Platform instance
        """
        self._platform = platform
        self._database_client = platform.database_client

        config_db, config_schema = self._platform.get_schema(AppSchemaID.APP_CONFIG)

        self._app_config_table = AppConfigTable(
            database_client=platform.database_client,
            database_name=config_db,
            schema_name=config_schema,
        )
        self._app_config = self._app_config_table.get()

        self._dmz_client = DmzClient(platform)
        csv_config = CSVConfig(header=True, separator=self._app_config.text_delimiter)
        self._dmz_export = DmzExport(
            database_client=platform.database_client,
            dmz_client=self._dmz_client,
            csv_config=csv_config,
            is_single_thread=self._platform.config.is_single_thread,
        )
        self._dmz_import = DmzImport(
            database_client=platform.database_client,
            dmz_client=self._dmz_client,
            csv_config=csv_config,
            is_single_thread=self._platform.config.is_single_thread,
        )

        self._clip_config_table = ClipConfigTable(
            database_client=platform.database_client,
            database_name=config_db,
            schema_name=config_schema,
        )

        # ClipJob
        self._clip_job_table = ClipJobTable(
            database_client=platform.database_client,
            database_name=config_db,
            schema_name=config_schema,
        )

        self._clip_input_table = ClipInputTable(platform)
        self._clip_output_table = ClipOutputTable(platform)
        self._clip_output_ref_table = ClipOutputReferenceTable(platform)

        contry_code = platform.config.locale.country_code
        match contry_code:
            case Country.US:
                self._clip_client = ClipClientUS(
                    platform=platform,
                    app_config=self._app_config,
                    clip_job_table=self._clip_job_table,
                    clip_output_table=self._clip_output_table,
                    dmz_export=self._dmz_export,
                    dmz_import=self._dmz_import,
                )
            case _:
                raise ClgxException(
                    error=CommonErrorCodes.CLIP_APP_CONFIG,
                    message=f"ClipClient is not supported for Country {contry_code}.",
                )

    @property
    def app_config(self) -> AppConfig:
        """App Config instance."""
        return self._app_config

    @property
    def app_config_table(self) -> AppConfigTable:
        """App Config Table instance."""
        return self._app_config_table

    @property
    def clip_config_table(self) -> ClipConfigTable:
        """App Config Table instance."""
        return self._clip_config_table

    @property
    def clip_job_table(self) -> ClipJobTable:
        """Clip Job Table instance."""
        return self._clip_job_table

    @property
    def clip_input_table(self) -> ClipInputTable:
        """Clip Input Table instance."""
        return self._clip_input_table

    @property
    def clip_output_table(self) -> ClipOutputTable:
        """Clip Output Table instance."""
        return self._clip_output_table

    @property
    def clip_output_ref_table(self) -> ClipOutputReferenceTable:
        """Clip Output Reference Table instance."""
        return self._clip_output_ref_table

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
            clip_config (ClipConfig): Clip configuration instance
            clip_job (ClipJob): Clip job instance
            row_counts (int): Total number of records to process
            input_query (str): SQL query string to fetch input data
            clip_input_mappings (dict): Mapping of Clip attributes to input column names
            stop_after_submit (bool, optional): If True, stop the process after submitting the job. Defaults to False.
            event_callback (callable, optional): Optional callback function to receive processing events.
        """
        self._clip_client.lookup(
            clip_config=clip_config,
            clip_job=clip_job,
            row_counts=row_counts,
            input_query=input_query,
            clip_input_mappings=clip_input_mappings,
            stop_after_submit=stop_after_submit,
            event_callback=event_callback,
        )
