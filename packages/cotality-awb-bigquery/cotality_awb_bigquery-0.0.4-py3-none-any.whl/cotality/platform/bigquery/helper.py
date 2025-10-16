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
"""GCP Helpers."""
from __future__ import annotations

import subprocess
from logging import getLogger

import google.auth

from ...core.clgxtyping import UserContext

logger = getLogger(__name__)


def set_user_context(user_context: UserContext):
    """
    Set the user context for the GCP platform.

    Args:
        user_context (UserContext): The user context to set.
    """
    credentials, project = google.auth.default()
    if credentials and hasattr(credentials, "service_account_email"):
        user_context.user_id = credentials.service_account_email  # type: ignore
    if not user_context.user_id or user_context.user_id == "default":
        user_context.user_id = get_gcloud_user_email()
    user_context.user_email = user_context.user_id
    user_context.organization = str(project)


def get_gcloud_user_email():
    """
    Gets the currently logged-in gcloud user's email by calling the gcloud CLI.

    This is the most reliable way to get the user's email in an interactive
    session, as it directly queries the gcloud configuration.

    Returns:
        str: The user's email address, or None if not found or on error.
    """
    user_email = "Unknown"
    unknown_user = "Unknown User"
    try:
        # The command to get the configured account email
        command = ["gcloud", "config", "get-value", "account"]

        # Run the command
        result = subprocess.run(
            command,
            capture_output=True,  # Capture the command's stdout and stderr
            text=True,  # Decode stdout/stderr as text
            check=True,  # Raise an exception if the command fails
        )

        # The email is the command's output, strip any whitespace
        email = result.stdout.strip()
        logger.info("Command: %s, Result: %s", " ".join(command), email)
        if not email:
            logger.error("Command: gcloud didn not return user email!")
        else:
            user_email = email

    except FileNotFoundError:
        logger.error("Error: 'gcloud' command not found.")
        logger.error(
            "Please ensure the Google Cloud SDK is installed and in your system's PATH."
        )

        return unknown_user
    except subprocess.CalledProcessError as e:
        logger.error("Error executing gcloud command: %s", e.stderr.strip())
        logger.error("Are you logged in? Try running 'gcloud auth login'.")
        return unknown_user
    except Exception as e:
        logger.error("An unexpected error occurred: %s", str(e))
        return unknown_user
    return user_email
