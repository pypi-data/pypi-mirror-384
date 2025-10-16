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
"""Clip Lookup - Job Status"""
from __future__ import annotations

import json
import logging
import time

from .....core.error_codes import CommonErrorCodes
from .....core.exception import ClgxException
from .....core.platform import Platform
from .....core.utils.dict import dict_snake_case
from .....core.utils.misc import datetime_to_int
from ...typing import ClipLookupAction
from ..clip_job import ClipJob, ClipJobStatus, ClipJobTable
from .typing import CLIP_STATUS_API

logger = logging.getLogger(__name__)


def execute(
    platform: Platform,
    clip_job: ClipJob,
    clip_job_table: ClipJobTable,
    stop_after_submit: bool = False,
) -> None:
    """Call batch API to submit clip data.

    Args:
        platform (Platform): Platform object
        clip_job (ClipJob): Clip job object
        clip_job_table (_ClipJobTable): Table to update clip job status
        stop_after_submit (bool): Whether to stop after submitting the job successfully
    """
    if clip_job.step >= ClipLookupAction.SUBMIT_JOB:
        logger.info("Checking status of Clip job ID: %s", clip_job.clip_job_id)
        dg_client = platform.digital_gateway_client
        headers = {"Content-Type": "application/json"}
        api = f"{CLIP_STATUS_API}/jobs/{clip_job.clip_job_id}"
        sleep_time = 60
        update_job_status_interval_in_seconds = (
            120  # 2 minutes since these are NOT OLTP databases
        )
        last_update_time = time.time()
        for attempt in range(1000):
            response = dg_client.get(
                api=api,
                headers=headers,
            )
            clip_status_response = dict_snake_case(json.loads(response.text))
            clip_job.clip_job_raw_status = clip_status_response.get(
                "current_status", ""
            )
            clip_job.clip_job_status = _clip_job_status(clip_job.clip_job_raw_status)
            match clip_job.clip_job_raw_status:
                case "ACCEPTED" | "EVALUATING" | "PENDING":
                    sleep_time = 60
                case "RUNNING":
                    sleep_time = 30
                    # This is for simulating resuming job testing
                    if stop_after_submit:
                        logger.info(
                            "Clip job %s is now running. Stopping as per configuration.",
                            clip_job.clip_job_id,
                        )
                        break
                case "SUMMARIZING":
                    sleep_time = 15
                case "COMPLETED" | "FAILED" | "CANCELLED":
                    message = f"Clip job {clip_job.clip_job_id} ended with status {clip_job.clip_job_status}, Details: {clip_status_response}"
                    if clip_job.clip_job_raw_status == "COMPLETED":
                        logger.info(message)
                    else:
                        raise ClgxException(
                            error=CommonErrorCodes.API_INVALID_RESPONSE, message=message
                        )
                    break
            logger.info(
                "Attempt %d: Clip job status: %s/%s. Response:%s",
                attempt + 1,
                clip_job.clip_job_raw_status,
                clip_job.clip_job_status,
                response.text,
            )
            if time.time() - last_update_time > update_job_status_interval_in_seconds:
                clip_job_table.update(clip_job)
                last_update_time = time.time()
            time.sleep(sleep_time)  # Exponential backoff

        if time.time() - last_update_time > update_job_status_interval_in_seconds:
            clip_job_table.update(clip_job)


# # ================ Private Functions ================
def _clip_job_status(job_status: str) -> ClipJobStatus:
    """Convert job status string to ClipJobStatus enum."""
    match job_status:
        case "ACCEPTED" | "EVALUATING" | "PENDING":
            return ClipJobStatus.SUBMITTED
        case "RUNNING" | "SUMMARIZING":
            return ClipJobStatus.RUNNING
        case "COMPLETED":
            return ClipJobStatus.COMPLETED
        case "FAILED":
            return ClipJobStatus.FAILED
        case "CANCELLED":
            return ClipJobStatus.CANCELED
        case _:
            logger.warning("Unknown job status:%s. Defaulting to UNKNOWN.", job_status)
            return ClipJobStatus.UNKNOWN
