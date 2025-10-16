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
"""HTTP IO"""
from __future__ import annotations

import logging

import requests
from pandas import DataFrame as PandaDataFrame

from ..core.clgxtyping import APIResponse, FileFormat
from ..core.platform import Platform

logger = logging.getLogger(__name__)


def upload_dataframe(
    platform: Platform,
    dataframe: PandaDataFrame,
    signed_url: str,
    file_format: FileFormat = FileFormat.CSV,
    chunk_size: int = 1000,
    timeout: int = 1 * 60 * 60,
) -> APIResponse:
    """Upload a DataFrame to the DMZ.

    Args:
        platform (Platform): Platform object
        dataframe (PandaDataFrame): DataFrame to upload
        url (str): URL to upload the DataFrame to
        format (FileFormat, optional): Format of the DataFrame. Defaults to FileFormat.CSV.
    """
    logger.debug("Uploading DataFrame to URL: %s", signed_url)
    response = APIResponse(
        success=True,
    )
    try:
        headers = platform.user_context.create_standard_headers()
        api_response = requests.put(
            url=signed_url,
            data=generate_data_chunks(
                dataframe=dataframe,
                file_format=file_format,
                chunk_size=chunk_size,
            ),
            headers=headers,
            timeout=timeout,
        )
        response.response_text = api_response.text
        response.status_code = api_response.status_code
        if api_response.status_code == 200:
            response.success = True
    except Exception as e:
        response.success = False
        response.error_message = f"Error uploading DataFrame. Reason:{str(e)}"
    return response


def generate_data_chunks(
    dataframe, file_format: FileFormat = FileFormat.CSV, chunk_size: int = 1000
):
    df_size = len(dataframe)
    loc = 0

    while loc < df_size:
        end_loc = min(loc + chunk_size, df_size)
        df_chunk = dataframe.iloc[loc:end_loc]
        if file_format == FileFormat.CSV:
            chunk = df_chunk.to_csv(index=False, header=loc == 0, sep="\t")
            yield chunk
        else:
            raise ValueError(f"Unsupported file format: {format}")
        loc += chunk_size
