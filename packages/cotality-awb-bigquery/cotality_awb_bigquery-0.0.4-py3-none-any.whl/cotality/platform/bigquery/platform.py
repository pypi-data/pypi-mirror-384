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
"""GCP Platform."""
from __future__ import annotations

import logging

from ...core.clgxtyping import Environment, Locale, PlatformType, UserContext
from ...core.logger import init_logger
from ...core.platform import Platform as PlatformAbstract
from .database import DatabaseClient
from .helper import set_user_context
from .secret import SecretClient


class GCPPlatform(PlatformAbstract):
    """
    Google Cloud Platform implementation.
    """

    def __init__(
        self, environment: Environment = Environment.PROD, locale: Locale = Locale.EN_US
    ) -> None:
        """Initialize the Google Cloud Platform.

        Args:
            environment (Environment, optional): The environment for the platform. Defaults to Environment.PROD.
            locale (Locale, optional): The locale for the platform. Defaults to Locale.EN_US.
        """
        init_logger()
        logger = logging.getLogger(__name__)
        database_client = DatabaseClient()
        secret_client = SecretClient(project_id=database_client.get_default_database())

        super().__init__(
            platform_type=PlatformType.BIGQUERY,
            database_client=database_client,
            secret_client=secret_client,
            env=environment,
            locale=locale,
            user_context=_get_user_context(),
            has_access_to_external_integration=True,
            inside_native_platform=True,
        )
        logger.info(
            "Google Cloud Platform initialized. User Context: %s", self.user_context
        )


def _get_user_context() -> UserContext:
    """Get the user context.

    Returns:
        UserContext: The user context.
    """
    # TO-DO: Get user context
    user_context = UserContext(platform_type=PlatformType.BIGQUERY)
    set_user_context(user_context)
    return user_context
