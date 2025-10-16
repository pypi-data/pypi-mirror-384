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
"""SQL types."""
from __future__ import annotations

import enum
from dataclasses import dataclass

from ...core.clgxtyping import UTF8

DEFAULT_ENCODING: str = UTF8
DEFAULT_FIELD_DELIMITER: str = "|"
DEFAULT_SKIP_LEADING_ROWS: int = 1
DEFAULT_QUOTE_CHARACTER: str = ""
DEFAULT_AUTO_DETECT: bool = False
DEFAULT_ESCAPE_QUOTA: bool = False
DEFAULT_ESCAPE_CHARACTER: str = ""
DEFAULT_NEW_LINE_MARKER: str = "\n"
DEFAULT_PARALLELISM_LEVEL: int = 4


# ======= Schema
class DataType(str, enum.Enum):
    """DataType Enum.

    Args:
        str (str): Value
        enum (enum.Enum): Name
    """

    # String
    TEXT = "text"
    VARCHAR = "varchar"
    CHARACTER = "char"
    # Number
    INTEGER = "integer"
    FLOAT = "float"
    DOUBLE = "double"

    # Logical
    BOOLEAN = "boolean"
    # Time & Date
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    # Spatial
    GEOGRAPHY = "geography"
    UNKNOWN = "unknown"


@dataclass(frozen=False)
class ColumnSchema:
    """Column Schema class.

    Args:
        name (str): Name of the column.
        data_type (DataType): Data type of the column.
        length (int): Length of the column. Only apply to CHAR and VARCHAR.
        0 means no limit.
        description (str): Description of the column.
        is_primary_key (bool): Is primary key.
        is_nullable (bool): Is nullable.
        is_unique (bool): Is unique.
    """

    name: str
    data_type: DataType
    length: int = 0
    description: str = ""
    is_primary_key: bool = False
    is_nullable: bool = True
    is_unique: bool = False


# ======= Misc
class WriteDisposition(str, enum.Enum):
    """WriteDisposition Enum.

    Args:
        str (str): Value
        enum (enum.Enum): Name
    """

    TRUNCATE = "truncate"
    DROP = "drop"
    APPEND = "append"
    EMPTY = "empty"


class CreateDisposition(str, enum.Enum):
    """CreateDisposition Enum.

    Args:
        str (str): Value
        enum (enum.Enum): Name
    """

    CREATE_IF_NEEDED = "create_if_needed"
    CREATE_NEVER = "create_never"


class IfExistAction(str, enum.Enum):
    """IfExistAction Enum.

    Args:
        str (str): Value
        enum (enum.Enum): Name
    """

    FAIL = "fail"
    APPEND = "append"
    REPLACE = "replace"
