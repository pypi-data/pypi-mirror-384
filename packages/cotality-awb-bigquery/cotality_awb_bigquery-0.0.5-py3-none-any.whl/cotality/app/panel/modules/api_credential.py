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

import panel as pn

from ....core.clgxtyping import LogLevel
from ...base.base_app import BaseApp


class ApiCredential:
    """API Credential management module."""

    def __init__(self, base_app: BaseApp, callback) -> None:
        """Initialize the API Credential module.

        Args:
            base_app (BaseApp): The base application instance.
            callback: The callback function to be called on save.
        """
        self._base_app = base_app
        self._callback = callback

        self._username_input = pn.widgets.TextInput(
            name=self._base_app._("Username"), placeholder="Enter username"
        )
        self._password_input = pn.widgets.PasswordInput(
            name=self._base_app._("Password"), placeholder="Enter password"
        )
        save_button = pn.widgets.Button(
            name=self._base_app._("Save"), button_type="primary"
        )

        self._panel = pn.Column(
            pn.pane.Markdown("## Cotality API Credentials"),
            self._username_input,
            self._password_input,
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
        if not self._username_input.value or not self._password_input.value:  # type: ignore
            self._base_app.display_message(
                LogLevel.ERROR, "Please enter both username and password."
            )
            return
        try:
            self._base_app.clip_client.save_digital_gateway_credential(self._username_input.value, self._password_input.value)  # type: ignore
            self._base_app.display_message(
                LogLevel.INFO, "Credentials saved successfully"
            )
            self._callback()
        except Exception as e:
            self._base_app.display_message(
                LogLevel.ERROR, f"Failed to save credentials: {str(e)}"
            )
