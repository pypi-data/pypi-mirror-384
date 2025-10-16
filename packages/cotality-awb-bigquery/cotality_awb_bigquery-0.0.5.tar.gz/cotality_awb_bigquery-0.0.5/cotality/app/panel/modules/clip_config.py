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
"""Clip Config module"""
from __future__ import annotations

import panel as pn

from ....core.clgxtyping import LogLevel
from ...base.base_app import BaseApp


class ClipConfig:
    """Clip Config module."""

    def __init__(self, base_app: BaseApp, callback) -> None:
        """Initialize the Clip Config module.

        Args:
            base_app (BaseApp): The base application instance.
            callback: The callback function to be called on save.
        """
        self._base_app = base_app
        self._callback = callback
        self._best_match = pn.widgets.Checkbox(name="Best match")
        self._google_standardization = pn.widgets.Checkbox(
            name="Google Standardization"
        )
        save_button = pn.widgets.Button(
            name=self._base_app._("Save"), button_type="primary"
        )

        self._panel = pn.Column(
            pn.pane.Markdown(
                "## Clip Configuration Options:"
                "### Return best match clip if check Otherwise multiple clips will be returned if there are multiple matches."
            ),
            pn.pane.Markdown(
                "- Best Match<br>"
                "Return best match clip if check Otherwise multiple clips will be returned if there are multiple matches."
            ),
            self._best_match,
            pn.pane.Markdown("- Fallback to Google Address Standardization"),
            self._google_standardization,
            save_button,
            sizing_mode="stretch_width",
        )
        save_button.on_click(self._save)

    @property
    def panel(self):
        return self._panel

    # =========== Private Methods ===========
    def _save(self, save_event):
        try:
            message = (
                f"Clip configuration saved successfully!<br>"
                f"Best Match: {self._best_match.value}<br>"
                f"Google Standardization: {self._google_standardization.value}"
            )
            self._base_app.display_message(LogLevel.INFO, message)
            self._callback()
        except Exception as e:
            self._base_app.display_message(
                LogLevel.ERROR, f"Failed to save clip configuration: {str(e)}"
            )
