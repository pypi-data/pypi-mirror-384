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
"""Snowflake Database client"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import toml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.snowpark import Session

from ...core.clgxtyping import UTF8, Environment
from ...core.exception import ClgxException, CommonErrorCodes

logger = logging.getLogger(__name__)

_CONNECTION = {
    Environment.UAT: ["connections", "cotality_app_uat"],
    Environment.PROD: ["connections", "cotality_app_pre_prod"],
    Environment.DEV: ["connections", "cotality_app_dev"],
}


def __load_private_key(key_file: str, passphrase: str) -> bytes:
    """Load the private key from a file.
    The private key is loaded using the cryptography library.
    The key is expected to be in PEM format and encrypted with a passphrase.
    The passphrase is used to decrypt the key.
    The decrypted key is returned as bytes.
    The key is expected to be in DER format and PKCS8 format.
    The key is returned as bytes.

    Args:
        key_file (str): Path to the private key file.
        passphrase (str): Passphrase to decrypt the private key.
    Raises:
        ClgxException: If the key file is not found or the passphrase is incorrect.
    Raises:
        ClgxException: If the key file is not in PEM format or not encrypted with the passphrase.

    Returns:
        bytes: The decrypted private key as bytes.
    """

    if not os.path.exists(key_file):
        raise ClgxException(
            error=CommonErrorCodes.IO_FILE_NOT_FOUND,
            parameters={"filename": key_file},
            message=f"Private key file not found: {key_file}",
        )

    try:
        with open(key_file, "rb") as key:
            private_key = serialization.load_pem_private_key(
                key.read(),
                password=passphrase.encode(),
                backend=default_backend(),
            )
    except Exception as err:
        raise ClgxException(
            error=CommonErrorCodes.IO_READ_FILE,
            parameters={"filename": key_file},
            message=f"Failed to load private key from file: {key_file}. Check file and passphase",
            cause=err,
        ) from err

    try:
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    except Exception as err:
        raise ClgxException(
            error=CommonErrorCodes.GEN_RUN_TIME,
            parameters={"filename": key_file},
            message=f"Failed to Encode: {key_file}",
            cause=err,
        ) from err

    return private_key_bytes


def build_sesssion(environment: Environment) -> Session:
    """Build a Snowflake session based on local cotality key.

    Returns:
        Session: Snowflake session object.
    """
    connection_name = _CONNECTION.get(environment)
    if not connection_name:
        raise ClgxException(
            error=CommonErrorCodes.GEN_INVALID_PARAMETER,
            parameters={"name": Environment},
            message=f"Could not find connection details {_CONNECTION} for environment {environment}",
        )

    config_file = f"{Path.home()}/.cotality/snowflake/config/config.toml"
    logger.info("Looking for file config_file %s...", config_file)

    if not os.path.exists(config_file):
        raise ClgxException(
            error=CommonErrorCodes.IO_FILE_NOT_FOUND,
            parameters={"filename": config_file},
            message=f"Could not find Snowflake Config file {config_file}",
        )

    try:
        with open(file=config_file, mode="r", encoding=UTF8) as file:
            config = toml.load(file)
    except Exception as err:
        raise ClgxException(
            error=CommonErrorCodes.IO_READ_FILE,
            parameters={"filename": config_file},
            message=f"Failed to load Snowflake Config file {config_file}",
            cause=err,
        ) from err

    try:
        connection_config = config[connection_name[0]][connection_name[1]]
    except KeyError as err:
        raise ClgxException(
            error=CommonErrorCodes.IO_INVALID_CONTENT,
            parameters={"filename": config_file},
            message=f"Could not find connection connection {connection_name} in {config_file}",
        ) from err

    key_file = os.path.expanduser(connection_config.get("private_key_file"))
    passphrase = os.path.expanduser(connection_config.get("private_key_file_pwd"))

    private_key = __load_private_key(key_file, passphrase)
    try:
        return Session.builder.configs(
            {
                "account": connection_config.get("account"),
                "user": connection_config.get("user"),
                "role": connection_config.get("role"),
                "database": connection_config.get("database"),
                "schema": connection_config.get("schema"),
                "warehouse": connection_config.get("warehouse"),
                "authenticator": connection_config.get("authenticator"),
                "private_key": private_key,
                "client_session_keep_alive": True,
            },
        ).create()
    except Exception as err:
        raise ClgxException(
            error=CommonErrorCodes.IO_DB_CONNECTION,
            parameters={"connection": _CONNECTION},
            message=f"Failed to connect to Snowflake: {_CONNECTION}",
            cause=err,
        ) from err
