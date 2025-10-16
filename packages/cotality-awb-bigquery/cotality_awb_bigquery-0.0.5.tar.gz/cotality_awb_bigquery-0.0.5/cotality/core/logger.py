# Copyright 2022 CORELOGIC
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
"""Logger."""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional

from .clgxtyping import PlatformType

# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    "LOG_HEADER_KEY_APPLICATION",
    "LOG_HEADER_KEY_ENVIRONMENT",
    "LOG_HEADER_KEY_PLATFORM_TYPE",
    "LOG_HEADER_KEY_INPUT",
    "LOG_HEADER_KEY_ACCOUNT",
    "LOG_HEADER_KEY_USER",
    "LOG_HEADER_KEY_ROLE",
    "LOG_HEADER_KEY_SERVER",
    "LOG_HEADER_KEY_DATABASE",
    "LOG_HEADER_KEY_SCHEMA",
    "set_log_header",
    "clear_log_headers",
    "debug_headers",
    "get_headers_string",
    "get_logger",
    "init_logger",
    "PlatformType",
]  # =============================================================================
# SIMPLEST POSSIBLE LOGGING - Monkey Patch Approach
# =============================================================================
LOG_HEADER_KEY_APPLICATION = "app"
LOG_HEADER_KEY_ENVIRONMENT = "env"
LOG_HEADER_KEY_PLATFORM_TYPE = "platform"
LOG_HEADER_KEY_INPUT = "input"
LOG_HEADER_KEY_ACCOUNT = "account"
LOG_HEADER_KEY_USER = "user"
LOG_HEADER_KEY_ROLE = "role"
LOG_HEADER_KEY_SERVER = "server"
LOG_HEADER_KEY_DATABASE = "db"
LOG_HEADER_KEY_SCHEMA = "schema"

_LOG_HEADERS = {
    LOG_HEADER_KEY_APPLICATION: "",
    LOG_HEADER_KEY_ENVIRONMENT: "",
    LOG_HEADER_KEY_PLATFORM_TYPE: "",
    LOG_HEADER_KEY_INPUT: "",
    LOG_HEADER_KEY_ACCOUNT: "",
    LOG_HEADER_KEY_USER: "",
    LOG_HEADER_KEY_ROLE: "",
    LOG_HEADER_KEY_SERVER: "",
    LOG_HEADER_KEY_DATABASE: "",
    LOG_HEADER_KEY_SCHEMA: "",
}


def set_log_header(header: Optional[Dict[str, str]] = None) -> None:
    """Update the Log header with the provided dictionary.

    Args:
        header: Dictionary with the log header values.
               If None, does nothing. If empty dict {}, clears all headers.
    """
    if header is not None:
        if header == {}:
            clear_log_headers()
        else:
            _LOG_HEADERS.update(header)


def clear_log_headers() -> None:
    """Clear all log headers completely."""
    _LOG_HEADERS.clear()
    _LOG_HEADERS.update(
        {
            LOG_HEADER_KEY_APPLICATION: "",
            LOG_HEADER_KEY_ENVIRONMENT: "",
            LOG_HEADER_KEY_PLATFORM_TYPE: "",
            LOG_HEADER_KEY_INPUT: "",
            LOG_HEADER_KEY_ACCOUNT: "",
            LOG_HEADER_KEY_USER: "",
            LOG_HEADER_KEY_ROLE: "",
            LOG_HEADER_KEY_SERVER: "",
            LOG_HEADER_KEY_DATABASE: "",
            LOG_HEADER_KEY_SCHEMA: "",
        }
    )


def debug_headers() -> Dict[str, str]:
    """Debug function to see what's actually in the headers dictionary."""
    return _LOG_HEADERS.copy()


def get_headers_string() -> str:
    """Get headers as a JSON string, excluding empty and None values."""
    # Filter out empty strings, None values, and whitespace-only strings
    filtered_headers = {
        k: v for k, v in _LOG_HEADERS.items() if v is not None and str(v).strip() != ""
    }

    if not filtered_headers:
        return ""

    # Return as JSON string with space prefix
    return " " + json.dumps(filtered_headers, separators=(",", ":"))


class CotalityLogger:
    """Custom logger wrapper that adds headers to log messages and works across all platforms."""

    def __init__(
        self, name: Optional[str] = None, platform_type: Optional[PlatformType] = None
    ):
        self._logger = logging.getLogger(name)
        self._platform_type = platform_type

        # Configure the logger for the specific platform if it doesn't have handlers
        if not self._logger.hasHandlers():
            self._configure_for_platform()

    def _configure_for_platform(self) -> None:
        """Configure logger based on platform type."""
        # Use consistent format across all platforms
        UNIVERSAL_FORMAT = "[%(asctime)s] [%(name)s:%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s"

        # Create a console handler that works across all environments
        handler = logging.StreamHandler(sys.stdout)

        # Use the same format for all platforms
        formatter = logging.Formatter(UNIVERSAL_FORMAT)

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

        # For BigQuery/Colab environments, don't propagate to avoid conflicts
        if self._platform_type == PlatformType.BIGQUERY:
            self._logger.propagate = False

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a debug message with headers."""
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(str(msg) + get_headers_string(), *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an info message with headers."""
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(str(msg) + get_headers_string(), *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a warning message with headers."""
        if self._logger.isEnabledFor(logging.WARNING):
            self._logger.warning(str(msg) + get_headers_string(), *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an error message with headers."""
        if self._logger.isEnabledFor(logging.ERROR):
            self._logger.error(str(msg) + get_headers_string(), *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log a critical message with headers."""
        if self._logger.isEnabledFor(logging.CRITICAL):
            self._logger.critical(str(msg) + get_headers_string(), *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Log an exception message with headers."""
        kwargs.setdefault("exc_info", True)
        self.error(msg, *args, **kwargs)

    # Forward all other attributes to the underlying logger
    def __getattr__(self, name: str) -> Any:
        return getattr(self._logger, name)


def get_logger(
    name: Optional[str] = None, platform_type: Optional[PlatformType] = None
) -> CotalityLogger:
    """Get a logger with header support that works across all platforms.

    Args:
        name: Name for the logger, typically __name__
        platform_type: The platform type (SNOWFLAKE, BIGQUERY, DATABRICKS)

    Returns:
        A CotalityLogger instance that automatically adds headers
    """
    return CotalityLogger(name, platform_type)


def init_logger(platform_type: Optional[PlatformType] = None) -> None:
    """Initialize the universal logger system.

    Args:
        platform_type: The platform type to configure logging for (SNOWFLAKE, BIGQUERY, DATABRICKS)
    """
    # Use consistent format across all platforms
    UNIVERSAL_FORMAT = (
        "[%(asctime)s] [%(name)s:%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s"
    )

    try:
        # Configure based on platform type
        if platform_type == PlatformType.BIGQUERY:
            # For BigQuery/Colab, use same format but force stdout and disable propagation
            logging.basicConfig(
                level=logging.INFO,
                format=UNIVERSAL_FORMAT,
                stream=sys.stdout,
                force=True,
            )
        elif platform_type == PlatformType.DATABRICKS:
            # For Databricks, ensure proper output to stdout
            logging.basicConfig(
                level=logging.INFO,
                format=UNIVERSAL_FORMAT,
                stream=sys.stdout,
                force=True,
            )
        elif platform_type == PlatformType.SNOWFLAKE:
            # For Snowflake environments
            logging.basicConfig(
                level=logging.INFO,
                format=UNIVERSAL_FORMAT,
                force=True,
            )
        else:
            # Default configuration for unknown platforms
            logging.basicConfig(
                level=logging.INFO,
                format=UNIVERSAL_FORMAT,
                force=True,
            )
    except Exception as e:
        print(f"Warning: Could not configure logging: {e}")
        print(f"Platform type: {platform_type}")

    clear_log_headers()
    logger = get_logger(__name__, platform_type)
    platform_name = platform_type.value if platform_type else "unknown"
    logger.info(f"Cotality Logger initialized for {platform_name} platform.")
