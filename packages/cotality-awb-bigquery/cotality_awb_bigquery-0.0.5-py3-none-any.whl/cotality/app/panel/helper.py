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
"""Panel helper"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import panel as pn

from ...core.clgxtyping import LogLevel
from ..base.base_app import BaseApp

TABULAR_SELECT_BUTTON = {"Select": "<i class='fa fa-search-location'></i>"}
MAIN_CONTENT_HEADER_PREFIX = "##"

BODY_CONTTENT_HEIGHT = 800


def init_panel(style_path: Optional[Path]):
    """Initialize Panel."""
    if style_path:
        pn.config.css_files = [str(style_path)]
    pn.extension(
        "terminal",
        "mathjax",
        "plotly",
        "vega",
        "deckgl",
        "tabulator",
        "stretch_width",
        css_files=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"
        ],
    )


def format_message(level: LogLevel, message: str) -> str:
    """
    Formatr message for display in the message area.

    Args:
        level (LogLevel): The level of the message
        message (str): The message to display
    """
    if level == LogLevel.ERROR:
        style = "color: red; background-color: #ffe6e6; padding: 10px; border: 1px solid red;"
    elif level == LogLevel.WARNING:
        style = "color: orange; background-color: #fff3cd; padding: 10px; border: 1px solid orange;"
    else:
        style = "color: green; background-color: #d4edda; padding: 10px; border: 1px solid green;"

    return f'<div style="{style}">{message}</div>'


def footer() -> pn.Row:
    """Create the footer for the application."""
    copyright_text = pn.pane.Markdown("© 2025 Cotality. All rights reserved.")
    return pn.Row(copyright_text, sizing_mode="stretch_width")


def show_processing(base_app: BaseApp) -> None:
    """Show the processing overlay."""
    overlay = pn.pane.HTML(base_app.processing_overlay_content)
    overlay.show()
