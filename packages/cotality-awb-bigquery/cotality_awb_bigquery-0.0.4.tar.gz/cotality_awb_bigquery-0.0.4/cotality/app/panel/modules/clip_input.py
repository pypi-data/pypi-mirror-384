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
"""Clip Input module"""
from __future__ import annotations

import panel as pn

from ....core.clgxtyping import LogLevel
from ...base.base_app import BaseApp


class ClipInput:
    """Clip Input management module."""

    def __init__(self, base_app: BaseApp, callback) -> None:
        """Initialize the Clip Input module.

        Args:
            base_app (BaseApp): The base application instance.
            callback: The callback function to be called on save.
        """
        self._base_app = base_app
        self._callback = callback

        self._input_name = pn.widgets.TextInput(
            name=self._base_app._("Input Name"), placeholder="Enter input table name"
        )
        save_button = pn.widgets.Button(
            name=self._base_app._("Save"), button_type="primary"
        )

        self._panel = pn.Column(
            pn.pane.Markdown("## Create new Clip input table"),
            self._input_name,
            save_button,
            sizing_mode="stretch_width",
        )

        save_button.on_click(self._save_credentials)

    @property
    def panel(self) -> pn.Column:
        """Get the panel for the API Credential module."""
        return self._panel

    # =============== Private Methods ===============
    def _save_credentials(self, save_event):
        if not self._input_name.value:  # type: ignore
            self._base_app.display_message(
                LogLevel.ERROR, "Please enter both input name and value."
            )
            return
        try:
            self._base_app.clip_client.create_clip_input(self._input_name.value, self._input_value.value)  # type: ignore
            self._base_app.display_message(LogLevel.INFO, "Input created successfully")
            self._callback()
        except Exception as e:
            self._base_app.display_message(
                LogLevel.ERROR, f"Failed to create input: {str(e)}"
            )
