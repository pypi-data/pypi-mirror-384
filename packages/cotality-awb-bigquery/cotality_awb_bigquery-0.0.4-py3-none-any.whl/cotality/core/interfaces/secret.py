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
"""Secret abstract/interface client."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SecretClient(ABC):
    """Secret Abstract Client."""

    def __init__(self) -> None:
        """Initialize the database client.

        Args:
            config (DbConfig): Database Configuration
        """

    @abstractmethod
    def get_digital_gateway_credential(self) -> tuple[str, str]:
        """Return username & password for Digital Gateway.

        Raises:
            ClgxException: Corelogic exception

        Returns:
            Tuple[str,str]: username, password
        """

    @abstractmethod
    def save_digital_gateway_credential(self, username: str, password: str) -> None:
        """Save the Digital Gateway credential.

        Args:
            username (str): Username for Digital Gateway
            password (str): Password for Digital Gateway

        Raises:
            ClgxException: Corelogic exception
        """
