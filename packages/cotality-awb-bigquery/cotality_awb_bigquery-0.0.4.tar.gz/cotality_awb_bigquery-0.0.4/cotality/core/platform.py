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
"""Platform Interface."""
from __future__ import annotations

from logging import getLogger
from typing import Tuple

from ..xapi.digital_gateway import DigitalGatewayClient
from .clgxtyping import (
    APIResponse,
    AppSchemaID,
    Environment,
    Locale,
    PlatformConfig,
    PlatformType,
    UserContext,
)
from .error_codes import CommonErrorCodes
from .exception import ClgxException
from .interfaces.database import DatabaseClient
from .interfaces.secret import SecretClient
from .locale import Localization, _Localization
from .plaform_app_db import AppDatabase

logger = getLogger(__name__)


class Platform:
    """Platform Interface.
    Args:
        ABC (_type_): Abstract Class
    """

    def __init__(
        self,
        platform_type: PlatformType,
        database_client: DatabaseClient,
        secret_client: SecretClient,
        locale: Locale = Locale.EN_US,
        env: Environment = Environment.PROD,
        user_context: UserContext = UserContext(),
        has_access_to_external_integration: bool = False,
        inside_native_platform: bool = True,
        is_single_thread: bool = True,
    ) -> None:
        """Initialize the Platform client.

        Args:
            platform_type (PlatformType): Platform type.
            database_client (DatabaseClient): Database client instance.
            secret_client (SecretClient): Secret client instance.
            locale (Locale): Locale for the platform.
            env (Environment): Environment for the platform.
            user_context (UserContext): User context for the platform.
            has_access_to_external_integration (bool): Flag to indicate access to external integration.
            is_single_thread (bool): Flag to indicate if the platform supports multi-threading.
        """
        self.__user_context = user_context
        logger.info(
            "Initializing Platform. Environment: %s, Locale: %s, Type:%s. Integration:%s, Native:%s, SSingle thread:%s",
            env,
            locale,
            platform_type,
            has_access_to_external_integration,
            inside_native_platform,
            is_single_thread,
        )
        self.__platform_config = PlatformConfig(
            platform_type=platform_type,
            locale=Locale(locale),
            inside_native_platform=inside_native_platform,
            has_access_to_external_integration=has_access_to_external_integration,
            is_single_thread=is_single_thread,
            environment=Environment(env),
        )
        logger.info("Platform Config: %s", self.__platform_config)
        self.__localization = Localization(
            str(self.__platform_config.locale), platform_type.value.upper()
        )
        self.__database_client = database_client
        self.__database_client.config.inside_native_platform = inside_native_platform
        self.__secret_client = secret_client
        self.__digital_gateway_client = self.__init_digital_gateway_client()
        self._app_database = AppDatabase(platform_type, database_client)
        self._app_database.validate_app_databases()

        logger.info("Base Platform initialized.")

    # ==== Application Databases
    @property
    def app_schemas(self) -> dict:
        """Get the application schemas."""
        return self._app_database.app_schemas

    def get_schema(self, schema_id: AppSchemaID) -> Tuple[str, str]:
        """Get the database for a specific application schema.

        Args:
            schema_id (AppSchemaID): The application schema identifier.

        Returns:
            Tuple[str, str]: A tuple containing the database name and schema name.
        """
        return self._app_database.get_schema(schema_id)

    @property
    def user_context(self) -> UserContext:
        """Return the user context.
        Returns:
            UserContext: User context.
        """
        return self.__user_context

    @property
    def database_client(self) -> DatabaseClient:
        """Return the database client.
        Returns:
            Database: Database client instance.
        """
        if self.__database_client:
            return self.__database_client
        raise ClgxException(
            error=CommonErrorCodes.GEN_INVALID_STATES,
            message="Database client is not initialized. Please call init_clients() first.",
        )

    @property
    def secret_client(self) -> SecretClient:
        """return the secret client.
        Returns:
            Secret: Secret client instance.
        """
        if self.__secret_client:
            return self.__secret_client
        raise ClgxException(
            error=CommonErrorCodes.GEN_INVALID_STATES,
            message="Secret client is not initialized. Please call init_clients() first.",
        )

    @property
    def digital_gateway_client(self) -> DigitalGatewayClient:
        """Return the digital gateway client.
        Returns:
            DigitalgatewayClient: Digital gateway client instance.
        """
        if self.__digital_gateway_client:
            return self.__digital_gateway_client
        raise ClgxException(
            error=CommonErrorCodes.GEN_INVALID_STATES,
            message="Digital Gateway client is not initialized. Please call init_clients() first.",
        )

    def set_digital_gatewaycredential(
        self, username: str, password: str
    ) -> APIResponse:
        """Set the Digital Gateway credentials.

        Args:
            username (str): Username for Digital Gateway.
            password (str): Password for Digital Gateway.
        """
        if not username or not password:
            response = APIResponse(
                success=False, error_message="Username and password cannot be empty."
            )
            return response
        if (
            self.__platform_config.platform_type == PlatformType.SNOWFLAKE
            and not self.__platform_config.has_access_to_external_integration
        ):
            response = self.__udf_set_digital_gateway_credential(
                username=username, password=password
            )
        else:
            try:
                token = self.__digital_gateway_client.set_credential(
                    username=username, password=password, validate=True
                )
                response = APIResponse(success=True, response_text=f"{token}")
            except Exception as e:
                response = APIResponse(success=False, error_message=str(e))
        return response

    def __udf_set_digital_gateway_credential(
        self, username: str, password: str
    ) -> APIResponse:
        """Set the Digital Gateway credentials using UDF.

        Args:
            username (str): Username for Digital Gateway.
            password (str): Password for Digital Gateway.
        """
        db_client = self.__database_client
        udf_name = "UDF_DIGITAL_GATEWAY_SET_CREDENTIAL"
        udf = f"{db_client.get_default_database()}.CLIP_APP.{udf_name}"
        try:
            sql = (f"CALL {udf}('{username}','{password}')").strip()
            dict_response = db_client.query_to_dict(sql)
            if (
                not dict_response
                or len(dict_response) == 0
                or (s := dict_response[0].get(udf_name.lower())) is None
            ):
                response = APIResponse(
                    success=False,
                    error_message=f"No response from the UDF: {udf}",
                )
            else:
                response = APIResponse.from_json(s if s else "{}")
        except Exception as e:
            response = APIResponse(
                success=False,
                error_message=f"Failed to set Digital Gateway credentials via UDF: {udf}, Reason: {e}",
            )
        return response

    @property
    def config(self) -> PlatformConfig:
        """Return the platform configuration.
        Returns:
            PlatformConfig: Platform configuration.
        """
        return self.__platform_config

    @property
    def localization(self) -> _Localization:
        """Get the localization instance.
        Returns:
            _Localization: Instance of the localization
        """
        return self.__localization

    def truncate_text_for_platform(self, error_message: str) -> str:
        """Truncate error message based on platform-specific TEXT/STRING limits.

        Args:
            error_message (str): The error message to truncate

        Returns:
            str: Truncated error message that fits platform limits
        """
        if not error_message:
            return ""

        # Define platform-specific limits (leaving some buffer for safety)
        platform_limits = {
            PlatformType.SNOWFLAKE: 16_000_000,  # 16MB limit, use 16M chars
            PlatformType.BIGQUERY: 2_600_000,  # ~2.5MB limit, use 2.6M chars
            PlatformType.DATABRICKS: 16_000_000,  # 2GB limit, but use reasonable 16M chars
        }

        max_length = platform_limits.get(
            self.__platform_config.platform_type, 4000
        )  # Default fallback

        if len(error_message) <= max_length:
            return error_message

        # Truncate and add indicator
        truncated = error_message[
            : max_length - 50
        ]  # Leave room for truncation message
        return (
            f"{truncated}... [TRUNCATED - Original length: {len(error_message)} chars]"
        )

    # =============== Private Methods ================
    def __init_digital_gateway_client(self) -> DigitalGatewayClient:
        """Initialize the Platform clients.

        Args:
        """
        username = ""
        password = ""
        try:
            username, password = self.__secret_client.get_digital_gateway_credential()
            logger.info(
                "Initializing Digital Gateway Client with username: %s, password: %s",
                username[0:3] + "****",
                password[0:3] + "****",
            )

        except Exception as e:
            logger.error("Failed to fetch Digital Gateway credentials: %s", e)

        digital_gateway_client = DigitalGatewayClient(
            username=username,
            password=password,
            environment=self.__platform_config.environment,
            country_code=self.__platform_config.locale.country_code,
        )
        logger.info("Platform initialized with Digital Gateway Client.")
        return digital_gateway_client
