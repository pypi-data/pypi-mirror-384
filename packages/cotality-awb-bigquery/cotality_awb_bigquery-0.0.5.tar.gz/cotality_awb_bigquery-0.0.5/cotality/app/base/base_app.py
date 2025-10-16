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
"""Application Base Class"""
from __future__ import annotations

import enum
import os
from datetime import datetime as dt
from logging import getLogger
from pathlib import Path
from typing import Optional, Tuple

from ...core.clgxtyping import AppCode, LogLevel
from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from ...core.platform import Platform
from ...xapi.clip.db_clip_client import ClipClient
from ...xapi.clip.private.clip_config import ClipConfig

logger = getLogger(__name__)


class UIFramework(str, enum.Enum):
    """Type of UI Frameworks, e.g. Streamlit, Panel."""

    STREAMLIT = "streamlit"
    PANEL = "panel"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class BaseApp:
    """Application Base Class
    This base class handles all common UI functionality:
    - Initialization of application resources
    - CSS/Styling based on UIFramework: Streamlit and Panel
    - Resource folder contains:
    - static: Contains static files (CSS, JS, images)
    - locales: Contains localization files
    - Platform contains platforms (Snowflake, Databricks, Bigquery) specific resources (eg. database and secret clients)
    - Resource folder contains application-specific resources:
        - locales: Contains localization files
        - static: Contains static files (CSS, JS, images)
    """

    def __init__(self, platform: Platform, ui_framework: UIFramework):
        """Initialize Application Base class.

        Args:
            platform (Platform): The platform instance to use. Contains Locale, Environment,
              and other platform-specific configurations, e.g. database, secret clients
            ui_framework (UIFramework): The UI framework to use.
        """
        try:
            self._platform = platform
            self._ui_framework = ui_framework
            self._init_success = False
            self._api_credential_is_valid = False
            self._get_text = lambda a: a  # palaceholder for get_text
            self._logo_content, self._logo_path = self._set_logo_content()
            self._image_path = Path(__file__).parent / "resources" / "static" / "images"
            self._images = {}
            self._style_content, self._style_path = self._set_style()
            self._processing_overlay_content = self._get_processing_overlay_content()
            # Initialize services
            self._clip_client = ClipClient(platform=self._platform)
            self._init_success = True
            self._icons = {}

        except ClgxException as e:
            logger.error("Error initializing BaseApp: %s", e)
            raise e
        except Exception as e:
            logger.error("Error initializing BaseApp: %s", e)
            raise ClgxException(
                error=CommonErrorCodes.CLIP_UNABLE_TO_INIT_BASE_APP,
                cause=e,
            ) from e

    def _(self, key: str):
        return self.platform.localization._(key)

    @property
    def init_success(self) -> bool:
        """Return whether the Base App was initialized successfully."""
        return self._init_success

    @property
    def logo_content(self) -> str:
        """Returns the logo content."""
        return self._logo_content

    @property
    def logo_path(self) -> Path:
        """Returns the logo path."""
        return self._logo_path

    @property
    def api_credential_is_valid(self) -> bool:
        """Return whether the API credentials are valid."""
        if not self._api_credential_is_valid:
            self._validate_api_credential()
        return self._api_credential_is_valid

    @property
    def platform(self) -> Platform:
        """Return the platform instance."""
        return self._platform

    @property
    def style(self) -> str:
        """Return the CSS style for the Streamlit App."""
        return self._style_content

    @property
    def style_path(self) -> Optional[Path]:
        """Returns the style path."""
        return self._style_path

    def image_path(self, name: str) -> Path:
        """Return the image path."""
        path = self._image_path / name
        if path.exists():
            return path
        return Path()

    @property
    def application_entitlements(self) -> list[AppCode]:
        """Return the application entitlements."""
        return [AppCode.CLIP]

    @property
    def clip_client(self) -> ClipClient:
        """Return the clip client instance."""
        return self._clip_client

    def set_app_content(self, content):
        """Set the contents of the application.

        Args:
            content: The (body) content to display.
        """

    def display_message(self, level: LogLevel, message: str) -> None:
        """Return localized message based on the message.

        Args:
            level (LogLevel): The log level for the message.
            message (str): The localization message.

        Returns:
            str: Localized message.
        """

    @property
    def footer_html_text(self) -> str:
        """Return the HTML text for the footer."""
        return f"""
            <div class="myfooter">
                &copy; {dt.now().year} Cotality. All rights reserved.
            </div>
        """

    @property
    def processing_overlay_content(self) -> str:
        """Return the HTML content for the processing overlay."""
        return self._processing_overlay_content

    # ============== Application services ==============
    def clip(
        self,
        input_tables: Optional[str] | Optional[list[str]] = None,
        limit: int = 0,
        stop_after_submit: bool = False,
        clip_config: Optional[ClipConfig] = None,
    ) -> None:
        """Run job to clip input table(s).
        If input_tables is not specified, all current input tables will be clipped.
        Pre-condition, API credentials must be valid.

        Args:
            input_tables (Optional[str] | Optional[list[str]], optional): _description_. Defaults to None.
            limit (int, optional): The maximum number of records to clip. Defaults to 0 (no limit).
            clip_step_stop_at (int, optional): Execute the clip steps up to this step (inclusive). Defaults to CLIP_STEP_LAST.
            stop_after_submit (bool, optional): Whether to stop the clip job after submitting it. Defaults to False.
            clip_config (Optional[ClipConfig], optional): The ClipConfig object. If None, the configuration will be fetched from the database. Defaults to None.
        """
        self._validate_api_credential()
        if isinstance(input_tables, str):
            itables = [input_tables]
        elif isinstance(input_tables, list):
            itables = input_tables
        else:
            itables = []

        if not itables or len(itables) == 0:
            itables = self.clip_client.get_clip_input_tables()

        for table in itables:
            self.clip_client.clip(
                input_table=table,
                limit=limit,
                stop_after_submit=stop_after_submit,
                clip_config=clip_config,
            )

    # ========== Private methods  ===

    def _validate_api_credential(self) -> None:
        """Validate API credential.
        - API username and password must be available.
        - API credentials must be valid.
        - This function will call Digital Gateway API (Apigee) to validate the credentials.
        """
        try:
            username, password = (
                self._platform.secret_client.get_digital_gateway_credential()
            )
            if username and password:
                logger.info("Validating API credentials for Digital Gateway")

                response = self._platform.set_digital_gatewaycredential(
                    username, password
                )
                self._api_credential_is_valid = response.success
                logger.info("API credentials validated successfully.")
            else:
                logger.warning("API credentials are missing.")
        except Exception as e:
            logger.error("Error validating API credentials: %s", e)
            # If there is an error, we assume the credentials are not valid
            self._api_credential_is_valid = False

    def _set_style(self) -> Tuple[str, Optional[Path]]:
        """Set the CSS style content and path.

        Returns:
            Tuple[str, Path]: The CSS style content and path.
        """
        try:
            style_content = ""
            # Loading streamlit/panel css
            style_path = (
                Path(__file__).parent
                / "resources"
                / "static"
                / f"style_{self._ui_framework}.css"
            )
            if style_path.exists():
                logger.info(
                    "Loading %s CSS style from: %s", self._ui_framework, style_path
                )

                style_content = style_content + style_path.read_text(encoding="UTF-8")
            else:
                logger.error("Streamlit/Panel CSS style file not found: %s", style_path)

                style_path = None
            # This should be handle from streamlit/panel
            # style_content = f"<style>{style_content}</style>"
        except Exception as e:
            logger.error("Error setting CSS styles: %s", e)
            style_content = ""
            style_path = None
            raise ClgxException(
                error=CommonErrorCodes.CLIP_UNABLE_TO_SET_CSS_STYLE,
                cause=e,
            ) from e

        return style_content, style_path

    def _set_logo_content(self) -> Tuple[str, Path]:
        """Return the logo content."""
        logo = ""
        logo_path = (
            Path(__file__).parent / "resources" / "static" / "images" / "logo.html"
        )
        if os.path.exists(logo_path):
            logo = logo_path.read_text(encoding="UTF-8")
        return logo, logo_path

    def _get_processing_overlay_content(self) -> str:
        """Return the processing overlay HTML content."""
        overlay = ""
        overlay_path = Path(__file__).parent / "resources" / "static" / "overlay.html"
        if overlay_path.exists():
            overlay = overlay_path.read_text(encoding="UTF-8")
            processing = self._("Processing...")
            overlay = overlay.replace("{{Processing}}", processing)
        return overlay
