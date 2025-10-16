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
"""Clip Base App"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from logging import getLogger

import pandas as pd
from dataclasses_json import DataClassJsonMixin

from ...core.decorator import SingletonMeta
from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from .base_app import BaseApp

logger = getLogger(__name__)


class ClipDashboardFlow(str, enum.Enum):
    """Clip Dashboard Flow - Navigation flow for the clip dashboard."""

    LIST_INPUTS = "list_inputs"
    INPUT_DETAIL = "input_detail"
    CLIPPING = "clipping"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class NavigationFlow(str, enum.Enum):
    """FieldViolationType - Violation type."""

    UNKNOWN = "unknown"
    DISPLAY_SECRET_ONLY = "display_secret_only"
    DISPLAY_INPUT_ONLY = "display_input_only"
    VIEW_DASHBOARD = "view_dashboard"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


@dataclass(init=True, frozen=False)
class Navigation(DataClassJsonMixin):
    """Navigation state."""

    flow: NavigationFlow = field(default_factory=lambda: NavigationFlow.UNKNOWN)
    enable_menu: dict = field(default_factory=lambda: {})
    input_table: str = field(default_factory=lambda: "")
    input_record_count: int = 0


class ClipBaseApp(metaclass=SingletonMeta):
    """Streamlit Base Application Client."""

    def __init__(self, base_app: BaseApp):
        """Initialize the Streamlit Base Application Client.

        Args:
            base_app (BaseApp): The base UI application instance to use.
            manage_secret_ui_callback: The UI component for managing secrets.
            create_input_ui_callback: The UI component for creating inputs.
            view_dashboard_ui_callback: The UI component for viewing the dashboard.
        """
        self._base_app = base_app

        # Application states
        self._navigation_flow = NavigationFlow.UNKNOWN
        self._secret_validated = False
        self._has_inputs = False

    @property
    def secret_validated(self) -> bool:
        """Return whether the secret has been validated."""
        return self._secret_validated

    @property
    def has_inputs(self) -> bool:
        """Return whether the application has inputs."""
        return self._has_inputs

    def get_navigation_flow(self) -> NavigationFlow:
        """
        Get the current navigation state.

        Returns:
            Navigation: The current navigation state.
        """
        if self._navigation_flow == NavigationFlow.UNKNOWN:
            # Validate for Secret, e.g. Digital Gateway credential
            # If not set:
            # Take user to enter new secret if can_manage_secret is True
            # Otherwise raise exception, e.g. User must enter the credential outside of this application
            username, password = (
                self._base_app.clip_client.get_digital_gateway_credential()
            )
            if not username or not password:
                if self._base_app.platform.config.can_manage_secret:
                    self._navigation_flow = NavigationFlow.DISPLAY_SECRET_ONLY
                else:
                    message = "Cotality Digital Gateway credentials are not set. Please set them and try again."
                    logger.error(message)
                    raise ClgxException(
                        error=CommonErrorCodes.GEN_INVALID_STATES, message=message
                    )
            else:
                self._secret_validated = True

            # Validate curent input tables.
            # If none, take user to create new input table
            input_tables = self._base_app.clip_client.get_clip_input_tables()
            if not input_tables or len(input_tables) == 0:
                self._navigation_flow = NavigationFlow.DISPLAY_INPUT_ONLY
            else:
                self._has_inputs = True
                self._navigation_flow = NavigationFlow.VIEW_DASHBOARD

        return self._navigation_flow

    def set_navigation(self, flow: NavigationFlow) -> None:
        """Set the navigation flow in the session state."""
        self._navigation_flow = flow

    def dataframe_locale_column_mapping(
        self, dataframe: pd.DataFrame
    ) -> dict[str, str]:
        """Return the summary columns for the dashboard input tables."""

        column_headers = {}
        for column in dataframe.columns:
            locale_column_name = self._base_app._(column)
            column_headers[column] = (
                locale_column_name if locale_column_name else column
            )
        return column_headers
