# Copyright 2022 COTALITY
#
# Licensed under the Apache License, "Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, "software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, "either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Error codes.

This module defines error codes used throughout the application for consistent error handling
and reporting. Each error code is associated with a specific error message template that can
be formatted with additional context information.

DO NOT modify this file manually.
All update or new error codes MUST be entered in this sheet:
https://docs.google.com/spreadsheets/d/13_7YrLf1B6vj9h4mSeLE0zLjf8YUuxHIk5eJOPiqxBo/edit?gid=353539354#gid=353539354

Then , just copy the code from Python code and paste in here
"""

from __future__ import annotations

import enum


class CommonErrorCodes(enum.Enum):
    """Common error codes."""

    GEN_ATTRIBUTE_NOT_DEFINED = ["GEN", 1, "Required attribute {name} is not defined"]
    GEN_INVALID_PARAMETER = ["GEN", 2, "Parameter {name} failed validation"]
    GEN_RUN_TIME = ["GEN", 3, "Unexpected runtime exception"]
    GEN_NOT_AVAILABLE = [
        "GEN",
        4,
        "This feature has not implemented or not available at this time",
    ]
    GEN_REQUIRED_PARAMETER = [
        "GEN",
        5,
        "Parameter {name} is required. It must be passed in and not empty",
    ]
    GEN_INVALID_STATES = ["GEN", 6, "Application states are not valid"]
    GEN_INVALID_STEP = [
        "GEN",
        7,
        "Requested step is not valid based on the current application states",
    ]
    GEN_ABSTRACT_FUNC_NOT_IMPLEMENTED = [
        "GEN",
        8,
        "This abstract function {name} was not impelented!",
    ]
    GEN_PIP_INSTALL = ["GEN", 9, "Failed to install package {name}:{version}"]
    GEN_WIZARD_STAGE_ERROR = ["GEN", 10, "Error occured while loading wizard stage"]
    GEN_TOO_MANY_RETRIES = ["GEN", 11, "Too many retries  from task {name}"]
    GEN_TIME_OUT = ["GEN", 12, "Time out from task {name}"]
    GEN_INVALID_DATA = ["GEN", 13, "Required data is in valid"]
    GEN_PERMISSION_DENIED = ["GEN", 14, "Permission denied for the request {name}"]

    IO_FILE_NOT_FOUND = ["IO", 1, "File {filename} not found"]
    IO_FILE_INVALID_FORMAT = [
        "IO",
        2,
        "Invalid file format , expecting {format} for url {url}",
    ]
    IO_URL_NOT_FOUND = ["IO", 3, "URL {url} not found"]
    IO_DB_CONNECTION = ["IO", 4, "Failed to connect to DB {connection}"]
    IO_URL_INVALID = ["IO", 5, "Invalid url {url}"]
    IO_FILE_JSON_ENCODE = ["IO", 6, "Failed to Encode to Json format"]
    IO_FILE_JSON_DECODE = ["IO", 7, "Failed to Decode to Json format"]
    IO_READ_FILE = ["IO", 8, "Read exception (filename}"]
    IO_WRITE_FILE = ["IO", 9, "Write exception (filename}"]
    IO_INVALID_CONTENT = ["IO", 10, "Invalid content in file {filename}"]

    API_GET_TOKEN = ["API", 1, "Failed to generate Apigee token"]
    API_AUTHENTICATION = ["API", 2, "Failed to authenticate"]
    API_PARSE_TOKEN = ["API", 3, "Failed to parse Apigee Token Response"]
    API_INVALID_RESPONSE = ["API", 4, "Invalid response"]
    API_INVALID_REQUEST = ["API", 5, "Invalid request "]
    API_AUTHORIZATION = ["API", 6, "Unable to authorize"]
    API_REST_FAILURE = ["API", 7, "Failed to call {url} rest end point"]
    API_DUPLICATE_RESOURCE = ["API", 8, "Duplicate resource found {resource}"]
    API_RESOURCE_NOT_FOUND = ["API", 9, "Resource not found {resource}"]
    API_SERVER_ERROR = ["API", 10, "Server error"]
    API_GCP_API = ["API", 11, "GCP API error"]
    API_INVALID_URL = ["API", 12, "Invalid URL: {name}"]

    AIRFLOW_NO_OUTPUT_STOP = [
        "AIRFLOW",
        1,
        "This task {name} produces no output. Auto stop retry and fail.",
    ]

    DB_GENERAL = ["DB", 1, ""]
    DB_MALFORMED_SQL = ["DB", 2, ""]
    DB_DUPLICATE_RESOURCE = ["DB", 3, "Duplicate resource found {resource}"]
    DB_RESOURCE_NOT_FOUND = ["DB", 4, "Resource not found {resource}"]
    DB_INVALID_SOURCE_SCHEMA = ["DB", 5, "Invalid schema for input source {name}"]
    DB_INVALID_SCHEMA_MAPPING = ["DB", 6, "Invalid schema mapping for {name}"]
    DB_FAILED_TO_CREATE_TABLE = ["DB", 7, "Failed to create table: {name}"]
    DB_FAILED_TO_DROP_TABLE = ["DB", 8, "Failed to drop table: {name}"]
    DB_FAILED_TO_EXECUTE_SQL = ["DB", 9, "Failed to execute command"]
    DB_FAILED_TO_QUERY_DATA = ["DB", 10, "Failed to run query"]
    DB_MISSING_PRIMARY_KEYS = [
        "DB",
        11,
        "This Model/Table doesn't have primary key {name}",
    ]

    SYS_GET_INSTANCE_METADATA = [
        "SYS",
        "1",
        "Failed to fetch metadata from instance {id}",
        "SYSTEM",
    ]
    SYS_CLOUD_FUNCTION_CALL = [
        "SYS",
        "2",
        "Failed to call cloud function <%=id%>",
        "SYSTEM",
    ]
    SYS_GET_ACCESS_TOKEN = ["SYS", "3", "Failed to create/fetch access token", "SYSTEM"]
    SYS_VAULT_LOGIN = ["SYS", "4", "Failed to login to Vault", "SYSTEM"]
    SYS_VAULT_FETCH_SECRETS = ["SYS", "5", "Failed to fetch Vault secrets", "SYSTEM"]

    CLIP_UNABLE_TO_INIT_BASE_APP = ["CLIP", 1, "Error initializing BaseApp!"]
    CLIP_UNABLE_TO_SET_CSS_STYLE = ["CLIP", 2, "Error setting CSS styles for the app!"]
    CLIP_LOCALE_PATH_NOT_FOUND = ["CLIP", 3, "Locale path not found: {path}"]
    CLIP_LOCALE_FILE_NOT_FOUND = ["CLIP", 4, "Locale file not found: {file}"]
    CLIP_INVALID_LOCALIZATION = ["CLIP", 5, "localization was not be able to setup!"]
    CLIP_UNABLE_TO_GET_SCHEMAS = ["CLIP", 6, "Failed to fetch schemas. Query: {query}"]
    CLIP_UNABLE_TO_GET_TABLES = ["CLIP", 7, "Failed to fetch tables. Query: {query}"]
    CLIP_UNABLE_TO_GET_RECORD_COUNT = [
        "CLIP",
        8,
        "Failed to fetch record count for table [{table}]. Query: {query}",
    ]
    CLIP_UNABLE_TO_GET_ROW_COUNT = [
        "CLIP",
        9,
        "Failed to fetch row count for tables [{tables}]. Query: {query}",
    ]
    CLIP_REJECTED_TO_LOCK_JOB = [
        "CLIP",
        10,
        "Job with ID {job_id} is already running for input table {input_table}.",
    ]
    CLIP_UNABLE_TO_LOCK_JOB = [
        "CLIP",
        11,
        "Failed to lock job for input table {input_table}.",
    ]
    CLIP_INVALID_SOURCE_SCHEMA = [
        "CLIP",
        12,
        "Missing required columns: {missing_columns} from table: {input_table}.",
    ]
    CLIP_DUPLICATE_RESOURCE = [
        "CLIP",
        13,
        "Found {non_unique_count} duplicated records for primary‐key {pk_column} from table: {input_table}.",
    ]
    CLIP_UNABLE_TO_PREPARE_REFERENCE_DATA = [
        "CLIP",
        14,
        "Failed to prepare input reference data. Input table: {input_table}, Reference output table: {ref_output_table}",
    ]
    CLIP_INVALID_TABLE_DATA = [
        "CLIP",
        15,
        "Input table {input_table} has invalid data that exceeds the threshold of {max_percentage}%. At least one of the following combinations must be present, such as:{street_address}, {zip_code}or {street_address}, {city}, {state}.",
    ]
    CLIP_JOB_ID_NOT_FOUND = ["CLIP", 16, "Job ID not found in the response: {response}"]
    CLIP_FAILED_TO_PARSE_API_RESPONSE = [
        "CLIP",
        17,
        "Failed to parse API response: {response}",
    ]
    CLIP_INVALID_CLIP_INPUT_TABLE = [
        "CLIP",
        18,
        "Could not find Clip iput table: {name}",
    ]
    CLIP_INVALID_CLIP_CONFIG_TABLE = [
        "CLIP",
        19,
        "Could not find Clip configuration table: {name}",
    ]
    CLIP_FAILED_TO_CREATE_TEMPORARY_TABLES = [
        "CLIP",
        20,
        "Failed to create temporary tables",
    ]
    CLIP_INVALID_CLIP_INPUT_SCHEMA = [
        "CLIP",
        21,
        "Clip input schema is invalid for table/view : {name}",
    ]
    CLIP_DUPLICATE_CLIP_INPUT_PRIMARY_KEY = [
        "CLIP",
        22,
        "Clip input contains duplicate in primary column: {name}",
    ]
    CLIP_TOO_MANY_FAILED_CLIP_INPUT_RECORDS = [
        "CLIP",
        23,
        "Too many invalid Clip input records found in table: {name}",
    ]
    CLIP_FAILED_TO_PREPARE_CLIP_INPUT_DATA = [
        "CLIP",
        24,
        "Failed to prepare Clip input data for table: {name}",
    ]
    CLIP_FAILED_TO_UPLOAD_CLIP_DATA = [
        "CLIP",
        25,
        "Failed to upload Clip input data for table: {name}",
    ]
    CLIP_FAILED_TO_CALL_CLIP_API = [
        "CLIP",
        26,
        "Failed to call Clip API for table: {name}",
    ]
    CLIP_FAILED_TO_CHECK_CLIP_JOB = [
        "CLIP",
        27,
        "Failed to check Clip job for table: {name}",
    ]
    CLIP_FAILED_TO_SAVE_CLIP_RESULTS = [
        "CLIP",
        28,
        "Failed to save Clip records to table: {name}",
    ]
    CLIP_APP_CONFIG = ["CLIP", 29, "Generic Application Configuration"]

    @property
    def parse(self) -> tuple[str, str, str, str]:
        """Parse and return error type, "code and message.

        Returns:
            Tuple[str, int, str, str]: [Type, Code, Message, SystemType]
        """
        size: int = len(self.value) if self.value else 0
        typ: str = self.value[0] if size >= 1 else "UNKNOWN"
        number: str = self.value[1] if size >= 2 else "0"
        message: str = self.value[2] if size >= 3 else ""
        system_type: str = self.value[3] if size >= 4 else ""
        return typ, number, message, system_type

    @property
    def error_type(self) -> str:
        """Return error type.

        Returns:
            str: Error type
        """
        size = len(self.value) if self.value else 0
        return str(self.value[0]) if size >= 1 else "UNKNOWN"

    @property
    def error_code(self) -> str:
        """Return error code.

        Returns:
            str: Error code.
        """
        size = len(self.value) if self.value else 0
        return f"{self.value[0]}-{self.value[1]}" if size >= 2 else "UNKNOWN-0"

    @property
    def message(self) -> str:
        """Return error message.

        Returns:
            str: Error message
        """
        size = len(self.value) if self.value else 0
        return self.value[2] if size >= 3 else ""

    @property
    def system_type(self) -> str:
        """Return system type.

        Returns:
            str: system type
        """
        size = len(self.value) if self.value else 0
        return self.value[3] if size >= 4 else ""
