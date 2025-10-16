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
"""API Credential module"""
from __future__ import annotations

import enum
from typing import Optional, Tuple

import panel as pn
from panel.models.tabulator import CellClickEvent
from param.parameterized import Event

from ....core.clgxtyping import LogLevel
from ....core.locales import keys as locale_keys
from ....xapi.clip import typing as clip_typing
from ...base import icons
from ...base.base_app import BaseApp
from ...panel import helper


class ContentType(str, enum.Enum):
    """AppCode - Application code."""

    MAIN = "main"
    INPUT = "input"
    CLIP_PROGRESS = "clip_progress"

    def __str__(self):
        """Return string.

        Returns:
            str: String
        """
        return str(self.value)


class InputListPanel:
    """Input list panel for the dashboard."""

    def __init__(self, base_app: BaseApp, local_css: str, callback) -> None:
        """Initialize the input list panel.

        Args:
            base_app (BaseApp): The base application instance.
            local_css (str): The local CSS styles for the panel.
            callback: The callback function to be called on input table selection.
        """
        self._base_app = base_app
        self._local_css = local_css
        self._callback = callback

        # Data
        self._input_tables_summary_dataframe = None

        # UI
        self._main_panel = self._create_main_panel()

    @property
    def panel(self) -> pn.Column:
        """Get the main panel for the job detail."""
        return self._main_panel

    def refresh(self):
        """Refresh the input list panel."""

    # ============== Private Methods ==============
    def _create_main_panel(self) -> pn.Column:

        refresh_button = pn.widgets.Button(
            name=f"{icons.REFRESH_ICON} Refresh",
            button_type="primary",
            width=120,
            margin=(5, 10),
        )
        clip_button = pn.widgets.Button(
            name=f"{icons.CLIP_ICON} Clip",
            button_type="primary",
            width=120,
            margin=(5, 10),
        )

        header = pn.Row(
            pn.pane.Markdown(self._base_app._(locale_keys.TEXT_DASHBOARD_START)),
            pn.Spacer(),
            refresh_button,
            clip_button,
            sizing_mode="stretch_width",
        )

        input_table_panel = pn.widgets.Tabulator(
            value=self._input_tables_summary_dataframe,
            buttons=helper.TABULAR_SELECT_BUTTON,
            sizing_mode="stretch_width",
            height=250,
            pagination="local",
            page_size=5,
            selectable=1,
            show_index=False,
            disabled=False,
        )

        return pn.Column(
            header,
            input_table_panel,
            min_height=300,
            margin=(0, 0, 20, 0),
            stylesheets=[self._local_css],
        )

    def _connect_events(self):
        """Connect event handlers to UI components."""


class JobPanel:
    """Job panel information."""

    def __init__(self, base_app: BaseApp, local_css: str) -> None:
        """Initialize the job panel.

        Args:
            base_app (BaseApp): The base application instance.
            clip_input_table (str): The name of the clip input table.
        """
        self._base_app = base_app
        self._local_css = local_css

        # Data
        self._clip_input_table = ""

        # UI
        self._main_panel = self._create_main_panel()

    @property
    def panel(self) -> pn.Column:
        """Get the main panel for the job detail."""
        return self._main_panel

    def refresh(self):
        """Refresh the input list panel."""

    def set_input_table(self, clip_input_table: str):
        self._clip_input_table = clip_input_table

    def hide(self):
        """Hide the job detail information."""
        self._main_panel.visible = False

    def show(self):
        """Show the job detail information."""
        self._main_panel.visible = True

    # ============== Private Methods ==============
    def _create_main_panel(self) -> pn.Column:
        return pn.Column()

    def _connect_events(self):
        """Connect event handlers to UI components."""


class ClipProgressPanel:
    """Clip progress panel for the dashboard."""

    def __init__(self, base_app: BaseApp, local_css: str, callback) -> None:
        """Initialize the clip progress panel.

        Args:
            base_app (BaseApp): The base application instance.
            clip_input_table (str): The name of the clip input table.
            callback: The callback function to be called on progress update.
        """
        self._base_app = base_app
        self._local_css = local_css
        self._callback = callback

        # Data
        self._clip_input_table = ""

        # UI
        self._main_panel = self._create_main_panel()

    @property
    def panel(self) -> pn.Column:
        """Get the main panel for the clip progress panel."""
        return self._main_panel

    def set_input_table(self, clip_input_table: str):
        """Set the input table for the clip progress panel.

        Args:
            clip_input_table (str): The name of the clip input table.
        """
        self._clip_input_table = clip_input_table

    # ============== Private Methods ==============
    def _create_main_panel(self) -> pn.Column:
        return pn.Column()

    def _connect_events(self):
        """Connect event handlers to UI components."""


class InputTablePanel:
    """Input table panel for the dashboard."""

    def __init__(self, base_app: BaseApp, local_css: str, callback) -> None:
        """Initialize the input table panel.

        Args:
            base_app (BaseApp): The base application instance.
            local_css (str): The local CSS styles for the panel.
            callback: The callback function to be called on create.
        """
        self._base_app = base_app
        self._local_css = local_css
        self._callback = callback

        # UI
        self._main_panel = self._create_main_panel()

    @property
    def panel(self) -> pn.Column:
        """Get the main panel for the input table panel."""
        return self._main_panel

    # ============== Private Methods ==============
    def _create_main_panel(self) -> pn.Column:
        return pn.Column()

    def _connect_events(self):
        """Connect event handlers to UI components."""


class ClipDashboard:
    """Dashboard management module."""

    def __init__(self, base_app: BaseApp, height: int = 700) -> None:
        """Initialize the Dashboard module.

        Args:
            base_app (BaseApp): The base application instance.
            height (int): The height of the dashboard.
        """
        self._base_app = base_app
        self._height = height

        # Data
        self._show_default_view = True

        # Instantiate sub-panels
        self._local_css = self._get_css_styles()
        self._input_list_panel = InputListPanel(
            base_app, self._local_css, self.select_input_table
        )
        self._job_panel = JobPanel(base_app, self._local_css)
        self._job_panel.hide()
        self._clip_progress_panel = ClipProgressPanel(
            base_app, self._local_css, self.select_input_table
        )
        self._input_table_panel = InputTablePanel(
            base_app, self._local_css, self.refresh
        )
        self._content_panel = pn.Column(
            self._input_list_panel.panel,
            self._job_panel.panel,
            width=1200,
            min_height=self._height,
            margin=(0, 50),
            stylesheets=[self._get_css_styles()],
        )
        self._main_panel = pn.Column(self._header(), self._content_panel)

    @property
    def panel(self) -> pn.Column:
        """Get the panel for the Dashboard module."""

        return self._main_panel

    def show_input_table_ui(self):
        """Display the input table panel."""
        self._content_panel.clear()
        self._content_panel.append(self._input_table_panel.panel)
        self._show_default_view = False

    def show_default_ui(self):
        """Display the default view."""
        self._content_panel.clear()
        self._content_panel.append(self._input_list_panel.panel)
        self._content_panel.append(self._job_panel.panel)
        self._show_default_view = True

    def select_input_table(self, input_table: str) -> None:
        """Select the input table for the dashboard.

        Args:
            input_table (str): The name of the table to select.
        """
        self._job_panel.show()
        self._job_panel.set_input_table(input_table)

    def refresh(self, input_table: str) -> None:
        """Callback function for the clip progress panel.

        Args:
            input_table (str): The name of the input table.
        """
        self.show_default_ui()
        self._input_list_panel.refresh()
        self.select_input_table(input_table)

    # =============== Private Methods ===============
    def _get_css_styles(self):
        """Return CSS styles for the dashboard."""
        return """
        .analysis-section {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            padding: 30px;
            border-left: 5px solid #007bff;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            margin-top: 25px;
            max-width: 100%;
        }

        .bk-root {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .panel-widget-box {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .tabulator {
            border-radius: 8px;
            overflow: hidden;
        }
        """

    def _header(self) -> pn.Row:
        """Create the header for the panel."""
        return pn.Row(
            pn.pane.Markdown(f"{helper.MAIN_CONTENT_HEADER_PREFIX} Clip Dashboard"),
            pn.Spacer(),
            sizing_mode="stretch_width",
            margin=(0, 0, 20, 0),
        )
