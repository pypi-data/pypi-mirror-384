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
String Utilities Module

This module provides utility functions for string manipulation, validation, and processing.
It includes functions for string replacement, formatting, validation, and other common
string operations used throughout the Cotality SDK.

The utilities are designed to handle edge cases gracefully and provide consistent behavior
across different string processing scenarios.

Author: Cotality Data Engineering Team
Version: 1.0.0
Last Updated: August 2025

Functions:
    string_replace: Replace a value in a string with another value
    snake_to_camel: Convert snake_case to camelCase (if implemented)
    validate_string: Validate string format and content (if implemented)
"""

from re import sub


# ==================== String Utilities ====================
def string_replace(source: str | None, replace_value: str, with_value: str) -> str:
    """Replace a value in a string with another value.

    Args:
        source (str): The source string.
        replace_value (str): The value to be replaced.
        with_value (str): The value to replace with.

    Returns:
        str: The modified string with the replaced value.
    """
    return source.replace(replace_value, with_value) if source else ""


def snake_case(text: str) -> str:
    """Convert string to snake case.

    Args:
        text (str): String

    Returns:
        str: Snake case string
    """
    return "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", text.replace("-", " "))
        ).split()
    ).lower()


def camel_case(text: str) -> str:
    """Convert to camel case.

    Args:
        text (str): Camel case string

    Returns:
        str: Camel case string
    """
    temp = text.split("_")
    return temp[0] + "".join(ele.title() for ele in temp[1:])
