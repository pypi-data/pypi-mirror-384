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
"""Clip Lookup - Submit"""
from __future__ import annotations

import json
import logging
from typing import Tuple

from requests import Response

from .....core.error_codes import CommonErrorCodes
from .....core.exception import ClgxException
from .....core.platform import Platform
from .....core.utils.dict import dict_camel_case, dict_snake_case
from ...typing import ClipLookupAction, ClipOutputReferenceColumns
from ..app_config import AppConfig
from ..clip_config import ClipConfig
from ..clip_job import ClipJob
from .typing import (
    CLIP_SUBMIT_API_V2,
    ClipAPIConfig,
    ClipSubmitAPI,
    ClipSubmitAPIRequest,
    ClipSubmitInput,
    ClipSubmitOutput,
)

logger = logging.getLogger(__name__)


def execute(
    platform: Platform,
    app_config: AppConfig,
    clip_config: ClipConfig,
    clip_job: ClipJob,
    input_bucket_location: str,
    output_bucket_location: str,
    clip_input_mappings: dict[str, str],
) -> None:
    """Call batch API to submit clip data.

    Args:
        platform (Platform): Platform object
        app_config (AppConfig): App configuration instance
        clip_config (ClipConfig): Configuration for the clip lookup
        clip_job (ClipJob): Clip job instance
        input_bucket_location (str): Input bucket location for the clip data
        output_bucket_location (str): Output bucket location for the clip data
        clip_input_mappings (dict[str, str]): Mappings for the clip input data
        event_callback (callable, optional): Optional callback function to receive processing events.
    Returns:
        APIResponse: Status of the upload operation
    """
    # clip_batch_response.clip_output_mappings = get_clip_output_mappings(CLIP_SUBMIT_API_V2)

    if clip_job.step == ClipLookupAction.UPLOAD_INPUT_DATA:
        logger.info("Submitting data to Clip API.")
        dg_client = platform.digital_gateway_client
        headers, request_payload = __api_request(
            platform=platform,
            app_config=app_config,
            clip_job=clip_job,
            clip_config=clip_config,
            input_bucket_location=input_bucket_location,
            output_bucket_location=output_bucket_location,
            clip_input_mappings=clip_input_mappings,
        )
        logger.info(
            "Submitting Clip job, URL: %s, Payload: %s, Headers: %s",
            CLIP_SUBMIT_API_V2,
            request_payload,
            headers,
        )
        response = dg_client.post(
            api=CLIP_SUBMIT_API_V2,
            data=request_payload,
            headers=headers,
        )
        __validate_response(response, clip_job)


# ================ Private Functions ================
JOB_ID_KEY = "jobID"


def __validate_response(response: Response, clip_job: ClipJob) -> None:
    """Parse the response from the API call.

    Args:
        response (Response): Response object from the API call
        clip_job (ClipJob): Clip job object to store job details
    Raises:
        ClgxException: If the response is not successful or does not contain job ID
    """
    try:
        if response.status_code == 200:
            clip_submit_response = dict_snake_case(response.json())
            clip_job.clip_job_id = clip_submit_response.get("job_id", "")
            if not clip_job.clip_job_id:
                raise ClgxException(
                    error=CommonErrorCodes.CLIP_JOB_ID_NOT_FOUND,
                    parameters={"response": response.text},
                )
    except Exception as e:
        raise ClgxException(
            error=CommonErrorCodes.CLIP_FAILED_TO_PARSE_API_RESPONSE,
            parameters={"response": response.text},
            cause=e,
        ) from e


def __api_request(
    platform: Platform,
    app_config: AppConfig,
    clip_job: ClipJob,
    clip_config: ClipConfig,
    input_bucket_location: str,
    output_bucket_location: str,
    clip_input_mappings: dict[str, str],
) -> Tuple[dict, str]:
    """Create API request for clip submission.

    Args:
        platform (Platform): Platform object
        app_config (AppConfig): App configuration instance
        clip_config (ClipConfig): Configuration for the clip lookup
        input_bucket_location (str): Input bucket location for the clip data
        output_bucket_location (str): Output bucket location for the clip data
    Returns:
        Tuple[dict, str]: API headers and request payload
    """
    headers = {"Content-Type": "application/json"}
    user_context = platform.user_context
    clip_api = ClipSubmitAPI(
        params=ClipAPIConfig(
            best_match=clip_config.best_match,
            google_fallback=clip_config.google_fallback,
            legacy_county_source=clip_config.legacy_county_source,
        )
    )
    clip_input = ClipSubmitInput(
        format=app_config.file_format,
        delimiter=app_config.text_delimiter,
        path=input_bucket_location,
        mappings=clip_input_mappings,
    )
    clip_output = ClipSubmitOutput(
        format=app_config.file_format,
        path=output_bucket_location,
        fields=[ClipOutputReferenceColumns.REFERENCE_ID.value],
    )
    request = ClipSubmitAPIRequest(
        request_id=clip_job.job_id,
        client_name=user_context.organization,
        api=clip_api,
        input=clip_input,
        output=clip_output,
    )
    request_camel_case = dict_camel_case(request.to_dict())
    request_payload = json.dumps(request_camel_case, ensure_ascii=True, indent=2)
    return headers, request_payload
