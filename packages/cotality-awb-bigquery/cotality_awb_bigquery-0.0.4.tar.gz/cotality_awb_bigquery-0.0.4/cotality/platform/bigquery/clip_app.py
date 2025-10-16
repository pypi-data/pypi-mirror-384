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
"""Bigquery Cotality Application Wrapper
Usages:
pip install cotality-platform-bigquery

from cotality.platform.bigquery.app import CotalityApp
app = CotalityApp()

To display the Application UI, call:
app.display()

For automation, call these services:
1. app.clip()

"""
from __future__ import annotations

from logging import getLogger

from ...app.panel.clip_app import ClipApp as ClipAppBase
from ...core.clgxtyping import Environment, Locale
from .platform import GCPPlatform

logger = getLogger(__name__)


class ClipApp(ClipAppBase):
    """Cotality application wrapper to intilize the platform"""

    def __init__(
        self, environment: Environment = Environment.PROD, locale: Locale = Locale.EN_US
    ):
        try:
            self._platform = GCPPlatform(environment=environment, locale=locale)
            logger.info("GCPPlatform initialized successfully.")
            super().__init__(self._platform)
            logger.info("CotalityApp initialized successfully.")
        except Exception as e:
            logger.error("Error initializing CotalityApp: %s", e)


def get_instance(
    environment: Environment = Environment.UAT, locale: Locale = Locale.EN_US
):
    """Get or create the singleton CotalityApp instance"""
    if not hasattr(get_instance, "instance") or get_instance.instance is None:
        get_instance.instance = ClipApp(environment=environment, locale=locale)
    return get_instance.instance
