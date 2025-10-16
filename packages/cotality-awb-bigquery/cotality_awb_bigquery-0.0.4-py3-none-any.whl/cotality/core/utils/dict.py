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
Dictionary Utilities Module

This module provides utility functions for dictionary manipulation, key transformation,
and data structure processing. It includes functions for converting key naming conventions,
merging dictionaries, and other common dictionary operations used throughout the Cotality SDK.

The utilities are designed to handle nested dictionaries, different data types, and edge
cases while maintaining data integrity and providing predictable behavior.

Author: Cotality Data Engineering Team
Version: 1.0.0
Last Updated: August 2025

Functions:
    dict_snake_case: Convert dictionary keys to snake_case format
    dict_camel_case: Convert dictionary keys to camelCase format (if implemented)
    merge_dictionaries: Merge multiple dictionaries with conflict resolution (if implemented)
    flatten_dict: Flatten nested dictionaries (if implemented)
"""

from typing import List

from .string import camel_case, snake_case


# ==================== Dictionary Utilities ====================
def dict_snake_case(iterable):
    """Convert the key name to snake case.

    Args:
        iterable (_type_): Iterable object ex: dict

    Returns:
        _type_: Iterable object with converted keys
    """
    return dict_case(iterable, snake_case)


def dict_camel_case(iterable):
    """Convert the key name to camel case.

    Args:
        iterable (_type_): Iterable object ex: dict

    Returns:
        _type_: Iterable object with converted keys
    """
    return dict_case(iterable, camel_case)


def dict_case(iterable, case_func):
    """Convert the key name using the callable function.

    Args:
        iterable (_type_): Iterable object ex: dict
        case_func (_type_): Case conversion function

    Returns:
        _type_: Iterable object with converted keys
    """
    new_dict = {}
    if isinstance(iterable, dict):
        for key in iterable.keys():
            new_key = case_func(key)
            if isinstance(iterable[key], dict):
                new_dict[new_key] = dict_case(iterable[key], case_func)
            elif isinstance(iterable[key], List):
                new_items = []
                for item in iterable[key]:
                    new_item = dict_case(item, case_func)
                    new_items.append(new_item)
                new_dict[new_key] = new_items
            else:
                new_dict[new_key] = iterable[key]
        return new_dict
    return iterable
