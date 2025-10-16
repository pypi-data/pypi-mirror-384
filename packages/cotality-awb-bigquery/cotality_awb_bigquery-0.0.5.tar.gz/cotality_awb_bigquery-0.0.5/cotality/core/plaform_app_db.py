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
"""Application Database Helper"""
from __future__ import annotations

import json
import logging
from typing import Tuple

from .clgxtyping import AppSchemaID, PlatformType
from .error_codes import CommonErrorCodes
from .exception import ClgxException
from .interfaces.database import DatabaseClient

logger = logging.getLogger(__name__)

_APP_SCHEMAS = {
    AppSchemaID.CLIP_INPUT,
    AppSchemaID.CLIP_OUTPUT,
    AppSchemaID.APP_CONFIG,
}

# Schema mapping for each platform
_SCHEMA_MAPPING = {
    PlatformType.SNOWFLAKE: {
        AppSchemaID.CLIP_INPUT: "clip_input",
        AppSchemaID.CLIP_OUTPUT: "clip_output",
        AppSchemaID.APP_CONFIG: "config",
    },
    PlatformType.BIGQUERY: {
        AppSchemaID.CLIP_INPUT: "cotality_app_clip_input",
        AppSchemaID.CLIP_OUTPUT: "cotality_app_clip_output",
        AppSchemaID.APP_CONFIG: "cotality_app_config",
    },
    PlatformType.DATABRICKS: {
        AppSchemaID.CLIP_INPUT: "COTALITY_APP_CLIP_INPUT",
        AppSchemaID.CLIP_OUTPUT: "COTALITY_APP_CLIP_OUTPUT",
        AppSchemaID.APP_CONFIG: "COTALITY_APP_CONFIG",
    },
}


class AppDatabase:
    """Application Database Helper"""

    def __init__(self, platform_type: PlatformType, db_client: DatabaseClient):
        """Initialize the AppDatabase helper.

        Args:
            platform_type (PlatformType): The platform type for the database.
            db_client (DatabaseClient): The database client instance.
        """
        logger.info("Initializing AppDatabase...")
        self._success = False
        self._db_client = db_client
        self._platform_type = platform_type

        self._app_databases = {}
        self._app_schemas = {}
        default_db = self._db_client.get_default_database()
        if not self._set_app_databases(default_db):
            logger.warning(
                "Not all application schemas found in default database: %s. Searching in all databases",
                default_db,
            )
            self._databases = self._db_client.get_databases()
            for db in self._databases:
                if self._set_app_databases(db):
                    break
        logger.info(
            "AppDatabase initialized. Schemas: %s",
            json.dumps(self._app_databases, indent=None),
        )

    @property
    def app_schemas(self) -> dict:
        """Get the application schemas."""
        return self._app_schemas

    def validate_app_databases(self) -> None:
        """Validate the application databases for a specific app code."""
        logger.info("Validating application databases...")
        for schema in _APP_SCHEMAS:
            if schema not in self._app_databases:
                raise ClgxException(
                    error=CommonErrorCodes.GEN_INVALID_STATES,
                    message=f"Could not find application schema: {schema} from {self._databases}. Please contact support.",
                )
            self._app_schemas[schema] = [
                self._app_databases[schema],
                _SCHEMA_MAPPING[self._platform_type][schema],
            ]
        logger.info(
            "All application databases are valid. %s",
            json.dumps(self._app_schemas, indent=0),
        )

    def get_schema(self, schema_id: AppSchemaID) -> Tuple[str, str]:
        """Get the database for a specific application schema.

        Args:
            schema_id (AppSchemaID): The application schema identifier.

        Returns:
            Tuple[str, str]: A tuple containing the database name and schema name.
        """
        return (
            self._app_databases.get(schema_id, ""),
            _SCHEMA_MAPPING[self._platform_type].get(schema_id, ""),
        )

    def _set_app_databases(self, database: str) -> bool:
        """Check if any of the schemas are in this database and register this database for the matched schema.

        Args:
            database (str): The database name.

        Returns:
            bool: True if all schemas are found, False otherwise.
        """
        schemas = self._db_client.get_schemas(database)
        schema_ids = _SCHEMA_MAPPING.get(self._platform_type, {})
        all_schemas_found = True
        for schema_id in schema_ids:
            if not self._app_databases.get(schema_id):
                for schema in schemas:
                    if schema_ids[schema_id] == schema:
                        self._app_databases[schema_id] = database
                if not self._app_databases.get(schema_id):
                    logger.info(
                        "Application schema: %s not found in database: %s",
                        schema_id,
                        database,
                    )
                    all_schemas_found = False
        return all_schemas_found
