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
"""Cotality Panel Application"""
from __future__ import annotations

import panel as pn

from ...core.clgxtyping import LogLevel
from ...core.platform import Platform
from ..base.base_app import BaseApp, UIFramework
from . import helper

MAIN_LAYOUT_MIN_HEIGHT = 1000
CONTENT_AREA_MIN_HEIGHT = 800


class ClipApp(BaseApp):
    """Panel Workbench Application Client."""

    def __init__(self, platform: Platform):
        """Initialize the Workbench Application Client.

        Args:
            platform (Platform): The platform instance to use.
        """
        super().__init__(
            platform=platform,
            ui_framework=UIFramework.PANEL,
        )
        self._ui_initialized = False

        # Initialize content area
        self._header_area = None
        self._message_area = None
        self._content_area = None
        self._footer_area = None
        self._main_layout = None

        self._glass_ui = pn.pane.HTML(
            self.processing_overlay_content,
            visible=False,
            sizing_mode="fixed",
            width=0,
            height=0,
        )

    def display_message(self, level: LogLevel, message: str) -> None:
        """Return localized message based on the message.

        Args:
            level (LogLevel): The log level for the message.
            message (str): The localization message.

        Returns:
            str: Localized message.
        """
        if self._message_area:
            self._message_area.object = helper.format_message(level, message)

    def set_app_content(self, content):
        """Set the contents of the application.

        Args:
            content: The (body) content to display.
            menu: The menu to display.

        """
        if content and self._content_area:
            self._content_area.clear()
            self._content_area.append(content)

    def display(self):
        """Display the application UI."""
        self._initialize_ui()
        if self._main_layout:
            pn.extension(sizing_mode="stretch_width")
            app_layout = pn.Column(
                self._main_layout, self._glass_ui, sizing_mode="stretch_width"
            )
            app_layout.servable()
            return app_layout
        raise RuntimeError("Main layout is not initialized.")

    def glass_mode(self):
        """Context manager for glass overlay"""
        self._glass_ui.visible = True
        try:
            yield
        finally:
            self._glass_ui.visible = False

    # ============ Private functions ============
    def _initialize_ui(self) -> None:
        if not self._ui_initialized:
            helper.init_panel(self.style_path)
            self._header_area = self.HeaderPanel()
            self._message_area = pn.pane.HTML("", sizing_mode="stretch_width")
            self._content_area = pn.Column(
                sizing_mode="stretch_width", min_height=CONTENT_AREA_MIN_HEIGHT
            )
            self._footer_area = pn.pane.HTML(self.footer_html_text)
            self._main_layout = pn.Column(
                self._header_area.panel,
                self._message_area,
                self._content_area,
                self._footer_area,
                sizing_mode="stretch_width",
                min_height=MAIN_LAYOUT_MIN_HEIGHT,
                scroll=True,
            )
            self._ui_initialized = True

    class HeaderPanel:
        # app_name = param.String(default="Cotality Application")
        logo = pn.pane.HTML(
            "<div style='width:50px;height:50px;background:#ccc;'>LOGO</div>"
        )

        def __init__(self):
            print("__init__")
            self._app_name = pn.pane.Markdown("# Cotality Application")
            self._header = pn.Row(self.logo, self._app_name)
            self._panel = pn.Row(self._header, pn.Spacer())

        def set_application_name(self, name: str):
            self._app_name.object = f"# {name}"

        @property
        def panel(self):
            return self._panel
