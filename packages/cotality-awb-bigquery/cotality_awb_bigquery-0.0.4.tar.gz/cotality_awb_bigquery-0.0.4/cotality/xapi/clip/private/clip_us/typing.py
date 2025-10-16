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
"""Clip Lookup Typing"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin

from ....dmz.typing import FileDownloadResponse, FileUploadResponse

CLIP_UPLOAD_API = "/signed-urls"
CLIP_SUBMIT_API_V2 = "/clip-batch"
CLIP_STATUS_API = "/clip-batch"
CLIP_DOWNLOAD_API = "/signed-urls"


@dataclass(init=True)
class ClipAPIConfig(DataClassJsonMixin):
    """Clip API Configuration."""

    best_match: bool = True
    google_fallback: bool = False
    legacy_county_source: bool = True


@dataclass(init=True, frozen=False)
class ClipSubmitAPI(DataClassJsonMixin):
    """ClipSubmitAPI request parameters."""

    endpoint: str = "universal"
    version: str = "v2"
    params: ClipAPIConfig = field(default_factory=ClipAPIConfig)


@dataclass(init=True, frozen=False)
class ClipSubmitInput(DataClassJsonMixin):
    """ClipSubmitInput request parameters."""

    format: str = "csv"
    delimiter: str = ","
    path: str = ""
    mappings: dict = field(default_factory=dict)


@dataclass(init=True, frozen=False)
class ClipSubmitOutput(DataClassJsonMixin):
    """ClipSubmitOutput request parameters."""

    format: str = "csv"
    path: str = ""
    fields: list[str] = field(default_factory=list)


@dataclass(init=True, frozen=False)
class ClipSubmitAPIRequest(DataClassJsonMixin):
    """ClipSubmitAPIRequest request payload."""

    request_id: str = ""
    client_name: str = ""
    api: ClipSubmitAPI = field(default_factory=ClipSubmitAPI)
    input: ClipSubmitInput = field(default_factory=ClipSubmitInput)
    output: ClipSubmitOutput = field(default_factory=ClipSubmitOutput)
