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
"""DMZ Client"""

import json
import logging

from ...core import constants
from ...core.decorator import SingletonMeta
from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from ...core.platform import Platform
from .typing import (
    DMZ_API,
    FileDownloadRequest,
    FileDownloadResponse,
    FileUploadRequest,
    FileUploadResponse,
)

logger = logging.getLogger(__name__)


class DmzClient(metaclass=SingletonMeta):
    """DMZ Client for file services."""

    def __init__(self, platform: Platform):
        self.__platform = platform

    def generate_signed_urls(
        self,
        request: FileUploadRequest,
    ) -> FileUploadResponse:
        """Generate signed URLs for file upload.

        Args:
            platform (Platform): Platform object
            request (FileUploadRequest): Request object containing upload details

        Returns:
            FileUploadResponse: Response containing signed URLs for the uploaded files
        """
        dg_client = self.__platform.digital_gateway_client
        headers, request_payload = self.__generate_signed_url_api_request(request)
        logger.info(
            "Generating signed URLs. API:%s, Credential:%s, Header:%s, Payload: %s",
            DMZ_API,
            dg_client.masked_credential,
            headers,
            request_payload,
        )
        response = dg_client.post(api=DMZ_API, data=request_payload, headers=headers)
        try:
            file_upload_response = FileUploadResponse.extract_from_dict(response.text)
            # TO-DO: This is a workaround for old API response. Remove this once we have new DMZ API in place.
            file_upload_response.post_init(file_upload_request=request)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f"Invalid Signed URL Upload response from DMZ API: {response}",
                cause=e,
            ) from e
        return file_upload_response

    def get_signed_urls(
        self,
        request: FileDownloadRequest,
    ) -> FileDownloadResponse:
        """Generate signed URLs for file upload.

        Args:
            platform (Platform): Platform object
            request (FileDownloadRequest): Request object containing download details

        Returns:
            FileDownloadResponse: Response containing signed URLs for the downloaded files
        """
        dg_client = self.__platform.digital_gateway_client
        headers = self.__get_signed_url_api_request(request)
        logger.info(
            "Getting signed URLs. API:%s, Credential:%s, Header:%s",
            DMZ_API,
            dg_client.masked_credential,
            headers,
        )

        response = dg_client.get(api=DMZ_API, headers=headers)
        try:
            return FileDownloadResponse.extract_from_dict(response.text)
        except Exception as e:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=f"Invalid Signed URL Download response from DMZ API: {response}",
                cause=e,
            ) from e

    # =============== Private Functions ================
    def __generate_signed_url_api_request(
        self,
        request: FileUploadRequest,
    ) -> tuple[dict, str]:
        """Prepare headers and request payload for the API call.

        Args:
            request (FileUploadRequest): Request object containing upload details

        Returns:
            tuple[dict, str]: Headers and JSON payload for the API call
        """
        # TO-DO: Remove HEADER_ACCESS_TYPE and action, once the new API is release.
        headers = self.__platform.user_context.create_standard_headers()
        # Override application ID to platform type specific value
        headers[constants.HEADER_STORAGE_ID] = request.storage_id
        headers[constants.HEADER_ACCESS_TYPE] = "public"
        if request.headers:
            headers.update(request.headers)

        request_json = json.dumps(
            {"action": "write", "path": request.path, "files": request.files}
        )
        return headers, request_json

    def __get_signed_url_api_request(
        self,
        request: FileDownloadRequest,
    ) -> dict:
        """Prepare headers for the API call.
        Args:
            platform (Platform): Platform object
            request (FileDownloadRequest): Request object containing download details
        Returns:
            dict: Headers and request payload for the API call
        """
        headers = self.__platform.user_context.create_standard_headers()
        headers[constants.HEADER_STORAGE_ID] = request.storage_id
        headers["PathLocation"] = request.path
        return headers
