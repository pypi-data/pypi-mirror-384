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
"""
Miscellaneous Utilities Module

This module provides various utility functions that don't fit into specific categories
but are commonly used throughout the Cotality SDK. It includes datetime utilities,
API response processing, logging helpers, and other general-purpose functions.

The utilities are designed to provide consistent behavior, proper error handling,
and integration with the broader SDK ecosystem.

Author: Cotality Data Engineering Team
Version: 1.0.0
Last Updated: August 2025

Functions:
    datetime_to_int: Convert datetime objects to integer timestamps
    process_api_response: Process API responses with standardized error handling
    configure_logging: Configure logging settings for the application
    validate_configuration: Validate configuration parameters
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from requests import Response

from ..clgxtyping import APIResponse

logger = logging.getLogger(__name__)


# ==================== DateTime Utilities ====================
def datetime_to_int(when: Optional[datetime] = None, day_offset: int = 0) -> int:
    """Convert datetime to integer timestamp.

    Args:
        when (datetime): DateTime object to convert.
        day_offset (int): Offset in days to apply to the datetime before conversion.

    Returns:
        int: Integer timestamp in seconds since epoch in the format YYYYMMDDHHMMSS.
    """
    value = 0
    if when is None:
        when = datetime.now(timezone.utc)
    if isinstance(when, datetime):
        if day_offset != 0:
            when = when + timedelta(days=day_offset)
        value = int(when.strftime("%Y%m%d%H%M%S"))
    return value


# ==================== API Utilities ====================
def to_api_response(
    api: str,
    api_response: Response,
    success_codes: list[int],
    request_id: str = "Unknown",
) -> APIResponse:
    """Create a standardized API response.

    Args:
        api (str): The API endpoint.
        api_response (Response): The HTTP response object.
        success_codes (list[int]): List of HTTP status codes that indicate success.
        request_id (str): Identifier for the request, default is "Unknown".

    Returns:
        APIResponse: A standardized API response object.
    """
    response = APIResponse(api=api, request_id=request_id)
    if api_response:
        response.status_code = api_response.status_code
        response.response_text = api_response.text
        if api_response.status_code in success_codes:
            response.success = True
            response.error_message = "OK"
        else:
            response.error_message = f"Failed to call API:{api}. Status code: {api_response.status_code}, Response: {api_response.text}"
    else:
        response.error_message = f"Failed to call API:{api}, No response!"
    return response
