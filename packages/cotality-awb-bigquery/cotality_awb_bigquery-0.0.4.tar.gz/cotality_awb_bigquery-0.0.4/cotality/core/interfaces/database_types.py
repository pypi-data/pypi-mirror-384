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
"""Database Type Mapping System.

This module provides comprehensive mapping between standardized DataTypeEnum and
platform-specific database types for Snowflake, BigQuery, and Databricks.

Key Components:
1. _DATATYPE_TO_DATABASE_MAPPING: Forward mapping (DataTypeEnum -> Database Type)
2. _DATABASE_TO_DATATYPE_MAPPING: Reverse mapping (Database Type -> DataTypeEnum)
3. _DATATYPE_TO_PANDAS_MAPPING: DataTypeEnum -> Pandas/NumPy dtype
4. _STRING_TO_DATATYPE_MAPPING: String representation -> DataTypeEnum
5. _NUMPY_TO_DATATYPE_MAPPING: NumPy type -> DataTypeEnum
6. _PYTHON_TO_DATATYPE_MAPPING: Python built-in type -> DataTypeEnum
7. get_database_data_type(): Convert enum to database type
8. get_datatype_from_database(): Convert database type back to enum
9. get_pandas_dtype_from_enum(): Convert enum to pandas dtype
10. convert_database_schema_to_datatypes(): Bulk schema conversion helper
11. convert_datatypes_to_pandas_schema(): Convert schema to pandas dtypes

This enables:
- Type-safe table creation across platforms
- Schema introspection and conversion
- Round-trip type conversions
- Platform-agnostic data type handling
- Efficient pandas DataFrame type conversions

Note: Mapping dictionaries (prefixed with _) are private implementation details.
      Use the public functions for type conversions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

import numpy as np

from ..clgxtyping import PlatformType


class DataTypeEnum(Enum):
    """Standard data type enumeration for database type mapping.

    This enum provides a clean, consistent way to specify data types
    across all database platforms, eliminating the mixed approach of
    NumPy types, Python types, and string identifiers.
    """

    # String types
    STRING = auto()
    TEXT = auto()

    # Integer types (signed)
    INT8 = auto()
    INT16 = auto()
    INT32 = auto()
    INT64 = auto()

    # Integer types (unsigned)
    UINT8 = auto()
    UINT16 = auto()
    UINT32 = auto()
    UINT64 = auto()

    # Float types
    FLOAT16 = auto()
    FLOAT32 = auto()
    FLOAT64 = auto()

    # Boolean
    BOOLEAN = auto()

    # Date/Time types
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    TIMESTAMP = auto()

    # Geometric types
    GEOMETRY = auto()
    POINT = auto()
    POLYGON = auto()
    LINESTRING = auto()
    MULTIPOINT = auto()
    MULTIPOLYGON = auto()
    MULTILINESTRING = auto()

    # Complex types
    JSON = auto()
    ARRAY = auto()
    DICTIONARY = auto()

    # Binary types
    BINARY = auto()
    BYTES = auto()


@dataclass(init=True, frozen=False)
class ColumnDefinition:
    """Column definition for database table creation.

    This class provides a clean, type-safe way to define table columns
    with all necessary metadata for SQL generation.
    """

    name: str  # Column name
    data_type: DataTypeEnum
    alias: str = ""  # Column alias
    description: str = ""  # Column description
    max_length: Optional[int] = None
    nullable: bool = True
    primary_key: bool = False
    default: Any = None
    group: str = ""

    def __post_init__(self):
        """Validate column definition after initialization."""

        # Set alias to name if not set
        if not self.alias:
            self.alias = self.name

        if self.max_length is not None and self.max_length <= 0:
            raise ValueError(f"max_length must be positive, got {self.max_length}")

        if not self.nullable and self.primary_key:
            # Primary keys are automatically NOT NULL, this is expected
            pass

        if self.data_type not in DataTypeEnum:
            raise ValueError(f"data_type must be a DataTypeEnum, got {self.data_type}")


# ========================================= Database Type Mappings =========================================

# Forward mapping: DataTypeEnum -> Native Database Type
# Maps from our standardized DataTypeEnum to platform-specific SQL data types
_DATATYPE_TO_DATABASE_MAPPING = {
    "SNOWFLAKE": {
        # String types
        "STRING": lambda max_len: f"VARCHAR({max_len})" if max_len else "VARCHAR",
        "TEXT": lambda max_len: f"VARCHAR({max_len})" if max_len else "VARCHAR",
        # Integer types (signed)
        "INT8": "TINYINT",
        "INT16": "SMALLINT",
        "INT32": "INTEGER",
        "INT64": "BIGINT",
        # Integer types (unsigned)
        "UINT8": "TINYINT",
        "UINT16": "SMALLINT",
        "UINT32": "INTEGER",
        "UINT64": "BIGINT",
        # Float types
        "FLOAT16": "FLOAT",
        "FLOAT32": "FLOAT",
        "FLOAT64": "DOUBLE",
        # Boolean
        "BOOLEAN": "BOOLEAN",
        # Date/Time types
        "DATE": "DATE",
        "TIME": "TIME",
        "DATETIME": "TIMESTAMP",
        "TIMESTAMP": "TIMESTAMP",
        # Geometric types
        "GEOMETRY": "GEOMETRY",
        "POINT": "GEOGRAPHY",
        "POLYGON": "GEOGRAPHY",
        "LINESTRING": "GEOGRAPHY",
        "MULTIPOINT": "GEOGRAPHY",
        "MULTIPOLYGON": "GEOGRAPHY",
        "MULTILINESTRING": "GEOGRAPHY",
        # Complex types
        "JSON": "VARIANT",
        "ARRAY": "ARRAY",
        "DICTIONARY": "OBJECT",
        # Binary types
        "BINARY": "BINARY",
        "BYTES": "VARBINARY",
    },
    "BIGQUERY": {
        # String types (BigQuery STRING has no length limit)
        "STRING": lambda max_len: "STRING",
        "TEXT": lambda max_len: "STRING",
        # Integer types (BigQuery consolidates all integers to INT64)
        "INT8": "INT64",
        "INT16": "INT64",
        "INT32": "INT64",
        "INT64": "INT64",
        "UINT8": "INT64",
        "UINT16": "INT64",
        "UINT32": "INT64",
        "UINT64": "INT64",
        # Float types (BigQuery consolidates all floats to FLOAT64)
        "FLOAT16": "FLOAT64",
        "FLOAT32": "FLOAT64",
        "FLOAT64": "FLOAT64",
        # Boolean
        "BOOLEAN": "BOOL",
        # Date/Time types
        "DATE": "DATE",
        "TIME": "TIME",
        "DATETIME": "TIMESTAMP",
        "TIMESTAMP": "TIMESTAMP",
        # Geometric types
        "GEOMETRY": "GEOGRAPHY",
        "POINT": "GEOGRAPHY",
        "POLYGON": "GEOGRAPHY",
        "LINESTRING": "GEOGRAPHY",
        "MULTIPOINT": "GEOGRAPHY",
        "MULTIPOLYGON": "GEOGRAPHY",
        "MULTILINESTRING": "GEOGRAPHY",
        # Complex types
        "JSON": "JSON",
        "ARRAY": "ARRAY",
        "DICTIONARY": "STRUCT",
        # Binary types
        "BINARY": "BYTES",
        "BYTES": "BYTES",
    },
    "DATABRICKS": {
        # String types (Databricks STRING has no length limit)
        "STRING": lambda max_len: "STRING",
        "TEXT": lambda max_len: "STRING",
        # Integer types
        "INT8": "TINYINT",
        "INT16": "SMALLINT",
        "INT32": "INT",
        "INT64": "BIGINT",
        "UINT8": "TINYINT",
        "UINT16": "SMALLINT",
        "UINT32": "INT",
        "UINT64": "BIGINT",
        # Float types
        "FLOAT16": "FLOAT",
        "FLOAT32": "FLOAT",
        "FLOAT64": "DOUBLE",
        # Boolean
        "BOOLEAN": "BOOLEAN",
        # Date/Time types
        "DATE": "DATE",
        "TIME": "STRING",  # Databricks doesn't have native TIME type
        "DATETIME": "TIMESTAMP",
        "TIMESTAMP": "TIMESTAMP",
        # Geometric types (Databricks stores geometry as WKT strings)
        "GEOMETRY": "STRING",
        "POINT": "STRING",
        "POLYGON": "STRING",
        "LINESTRING": "STRING",
        "MULTIPOINT": "STRING",
        "MULTIPOLYGON": "STRING",
        "MULTILINESTRING": "STRING",
        # Complex types
        "JSON": "STRING",  # Store as JSON string
        "ARRAY": "ARRAY<STRING>",
        "DICTIONARY": "MAP<STRING,STRING>",
        # Binary types
        "BINARY": "BINARY",
        "BYTES": "BINARY",
    },
}


# Reverse mapping: Native Database Type -> DataTypeEnum
# Maps from platform-specific SQL data types back to our standardized DataTypeEnum
_DATABASE_TO_DATATYPE_MAPPING = {
    "SNOWFLAKE": {
        # String types
        "VARCHAR": "STRING",
        "STRING": "STRING",
        "TEXT": "TEXT",
        "CHAR": "STRING",
        # Integer types
        "TINYINT": "INT8",
        "SMALLINT": "INT16",
        "INTEGER": "INT32",
        "INT": "INT32",
        "BIGINT": "INT64",
        "NUMBER": "INT64",  # Snowflake's generic numeric
        # Float types
        "FLOAT": "FLOAT32",
        "DOUBLE": "FLOAT64",
        "REAL": "FLOAT32",
        "DECIMAL": "FLOAT64",
        "NUMERIC": "FLOAT64",
        # Boolean
        "BOOLEAN": "BOOLEAN",
        "BOOL": "BOOLEAN",
        # Date/Time types
        "DATE": "DATE",
        "TIME": "TIME",
        "TIMESTAMP": "TIMESTAMP",
        "DATETIME": "DATETIME",
        "TIMESTAMP_NTZ": "TIMESTAMP",
        "TIMESTAMP_LTZ": "TIMESTAMP",
        "TIMESTAMP_TZ": "TIMESTAMP",
        # Geometric types
        "GEOMETRY": "GEOMETRY",
        "GEOGRAPHY": "POINT",  # Default to POINT for geography
        # Complex types
        "VARIANT": "JSON",
        "OBJECT": "DICTIONARY",
        "ARRAY": "ARRAY",
        # Binary types
        "BINARY": "BINARY",
        "VARBINARY": "BYTES",
    },
    "BIGQUERY": {
        # String types
        "STRING": "STRING",
        "BYTES": "BYTES",
        # Integer types
        "INT64": "INT64",
        "INTEGER": "INT64",
        # Float types
        "FLOAT64": "FLOAT64",
        "FLOAT": "FLOAT64",
        "NUMERIC": "FLOAT64",
        "DECIMAL": "FLOAT64",
        "BIGNUMERIC": "FLOAT64",
        "BIGDECIMAL": "FLOAT64",
        # Boolean
        "BOOL": "BOOLEAN",
        "BOOLEAN": "BOOLEAN",
        # Date/Time types
        "DATE": "DATE",
        "TIME": "TIME",
        "DATETIME": "DATETIME",
        "TIMESTAMP": "TIMESTAMP",
        # Geometric types
        "GEOGRAPHY": "GEOMETRY",
        # Complex types
        "JSON": "JSON",
        "STRUCT": "DICTIONARY",
        "RECORD": "DICTIONARY",
        "ARRAY": "ARRAY",
        "REPEATED": "ARRAY",
    },
    "DATABRICKS": {
        # String types
        "STRING": "STRING",
        "VARCHAR": "STRING",
        "CHAR": "STRING",
        # Integer types
        "TINYINT": "INT8",
        "SMALLINT": "INT16",
        "INT": "INT32",
        "INTEGER": "INT32",
        "BIGINT": "INT64",
        "LONG": "INT64",
        # Float types
        "FLOAT": "FLOAT32",
        "DOUBLE": "FLOAT64",
        "DECIMAL": "FLOAT64",
        "NUMERIC": "FLOAT64",
        # Boolean
        "BOOLEAN": "BOOLEAN",
        "BOOL": "BOOLEAN",
        # Date/Time types
        "DATE": "DATE",
        "TIMESTAMP": "TIMESTAMP",
        "INTERVAL": "STRING",  # Databricks interval as string
        # Complex types (Databricks stores these as strings)
        "ARRAY": "ARRAY",
        "MAP": "DICTIONARY",
        "STRUCT": "DICTIONARY",
        # Binary types
        "BINARY": "BINARY",
    },
}


# Reverse mapping: DataTypeEnum -> Pandas/NumPy dtype
# Maps from our standardized DataTypeEnum to pandas-compatible data types
# NOTE: Using nullable types (Int64, StringDtype, etc.) to handle NA/blank values
_DATATYPE_TO_PANDAS_MAPPING = {
    # String types - using nullable StringDtype for better NA handling
    DataTypeEnum.STRING: "string",  # Pandas nullable string
    DataTypeEnum.TEXT: "string",  # Pandas nullable string
    # Integer types (signed) - using nullable Int types to handle NA/blank values
    DataTypeEnum.INT8: "Int8",  # Pandas nullable Int8
    DataTypeEnum.INT16: "Int16",  # Pandas nullable Int16
    DataTypeEnum.INT32: "Int32",  # Pandas nullable Int32
    DataTypeEnum.INT64: "Int64",  # Pandas nullable Int64
    # Integer types (unsigned) - using nullable UInt types to handle NA/blank values
    DataTypeEnum.UINT8: "UInt8",  # Pandas nullable UInt8
    DataTypeEnum.UINT16: "UInt16",  # Pandas nullable UInt16
    DataTypeEnum.UINT32: "UInt32",  # Pandas nullable UInt32
    DataTypeEnum.UINT64: "UInt64",  # Pandas nullable UInt64
    # Float types - floats handle NA natively with np.nan
    DataTypeEnum.FLOAT16: np.float16,
    DataTypeEnum.FLOAT32: np.float32,
    DataTypeEnum.FLOAT64: np.float64,
    # Boolean - using nullable boolean to handle NA/blank values
    DataTypeEnum.BOOLEAN: "boolean",  # Pandas nullable boolean
    # Date/Time types
    DataTypeEnum.DATE: "datetime64[ns]",
    DataTypeEnum.TIME: "object",  # Time as string
    DataTypeEnum.DATETIME: "datetime64[ns]",
    DataTypeEnum.TIMESTAMP: "datetime64[ns]",
    # Geometric types (stored as strings in pandas)
    DataTypeEnum.GEOMETRY: "object",
    DataTypeEnum.POINT: "object",
    DataTypeEnum.POLYGON: "object",
    DataTypeEnum.LINESTRING: "object",
    DataTypeEnum.MULTIPOINT: "object",
    DataTypeEnum.MULTIPOLYGON: "object",
    DataTypeEnum.MULTILINESTRING: "object",
    # Complex types (stored as objects in pandas)
    DataTypeEnum.JSON: "object",
    DataTypeEnum.ARRAY: "object",
    DataTypeEnum.DICTIONARY: "object",
    # Binary types
    DataTypeEnum.BINARY: "object",
    DataTypeEnum.BYTES: "object",
}


# String to DataTypeEnum mapping for _normalize_dtype_key
_STRING_TO_DATATYPE_MAPPING = {
    # String types
    "string": DataTypeEnum.STRING,
    "str": DataTypeEnum.STRING,
    "object": DataTypeEnum.STRING,
    "text": DataTypeEnum.TEXT,
    # Integer types
    "int8": DataTypeEnum.INT8,
    "int16": DataTypeEnum.INT16,
    "int32": DataTypeEnum.INT32,
    "int64": DataTypeEnum.INT64,
    "uint8": DataTypeEnum.UINT8,
    "uint16": DataTypeEnum.UINT16,
    "uint32": DataTypeEnum.UINT32,
    "uint64": DataTypeEnum.UINT64,
    # Float types
    "float16": DataTypeEnum.FLOAT16,
    "float32": DataTypeEnum.FLOAT32,
    "float64": DataTypeEnum.FLOAT64,
    "double": DataTypeEnum.FLOAT64,
    # Boolean
    "bool": DataTypeEnum.BOOLEAN,
    "boolean": DataTypeEnum.BOOLEAN,
    # Date/Time types
    "date": DataTypeEnum.DATE,
    "time": DataTypeEnum.TIME,
    "datetime": DataTypeEnum.DATETIME,
    "datetime64": DataTypeEnum.DATETIME,
    "datetime64[ns]": DataTypeEnum.DATETIME,
    "timestamp": DataTypeEnum.TIMESTAMP,
    # Geometric types
    "geometry": DataTypeEnum.GEOMETRY,
    "point": DataTypeEnum.POINT,
    "polygon": DataTypeEnum.POLYGON,
    "linestring": DataTypeEnum.LINESTRING,
    "multipoint": DataTypeEnum.MULTIPOINT,
    "multipolygon": DataTypeEnum.MULTIPOLYGON,
    "multilinestring": DataTypeEnum.MULTILINESTRING,
    # Complex types
    "json": DataTypeEnum.JSON,
    "array": DataTypeEnum.ARRAY,
    "dict": DataTypeEnum.DICTIONARY,
    # Binary types
    "bytes": DataTypeEnum.BYTES,
    "binary": DataTypeEnum.BINARY,
}


# NumPy to DataTypeEnum mapping for _normalize_dtype_key
_NUMPY_TO_DATATYPE_MAPPING = {
    np.str_: DataTypeEnum.STRING,
    np.object_: DataTypeEnum.STRING,
    np.int8: DataTypeEnum.INT8,
    np.int16: DataTypeEnum.INT16,
    np.int32: DataTypeEnum.INT32,
    np.int64: DataTypeEnum.INT64,
    np.uint8: DataTypeEnum.UINT8,
    np.uint16: DataTypeEnum.UINT16,
    np.uint32: DataTypeEnum.UINT32,
    np.uint64: DataTypeEnum.UINT64,
    np.float16: DataTypeEnum.FLOAT16,
    np.float32: DataTypeEnum.FLOAT32,
    np.float64: DataTypeEnum.FLOAT64,
    np.bool_: DataTypeEnum.BOOLEAN,
    np.datetime64: DataTypeEnum.DATETIME,
    np.bytes_: DataTypeEnum.BYTES,
}


# Python built-in to DataTypeEnum mapping for _normalize_dtype_key
_PYTHON_TO_DATATYPE_MAPPING = {
    str: DataTypeEnum.STRING,
    int: DataTypeEnum.INT64,
    float: DataTypeEnum.FLOAT64,
    bool: DataTypeEnum.BOOLEAN,
    bytes: DataTypeEnum.BYTES,
}


def _normalize_dtype_key(dtype) -> DataTypeEnum:
    """Normalize dtype input to a consistent DataTypeEnum for lookup.

    Args:
        dtype: Input data type (can be DataTypeEnum, numpy type, python type, or string)

    Returns:
        Normalized DataTypeEnum for DTYPE_MAPPING lookup
    """

    # If already a DataTypeEnum, return as-is
    if isinstance(dtype, DataTypeEnum):
        return dtype

    # Handle string representations
    if isinstance(dtype, str):
        if dtype in _STRING_TO_DATATYPE_MAPPING:
            return _STRING_TO_DATATYPE_MAPPING[dtype]
        raise ValueError(f"Unknown string data type: {dtype}")

    # Handle numpy array instances (get the type from dtype)
    if hasattr(dtype, "dtype") and hasattr(dtype.dtype, "type"):
        numpy_type = dtype.dtype.type
        if numpy_type in _NUMPY_TO_DATATYPE_MAPPING:
            return _NUMPY_TO_DATATYPE_MAPPING[numpy_type]

    # Handle numpy dtype objects
    if hasattr(dtype, "type") and dtype.type in _NUMPY_TO_DATATYPE_MAPPING:
        return _NUMPY_TO_DATATYPE_MAPPING[dtype.type]

    # Direct numpy type lookup
    if dtype in _NUMPY_TO_DATATYPE_MAPPING:
        return _NUMPY_TO_DATATYPE_MAPPING[dtype]

    # Handle Python built-in types
    if dtype in _PYTHON_TO_DATATYPE_MAPPING:
        return _PYTHON_TO_DATATYPE_MAPPING[dtype]

    raise ValueError(f"Unsupported data type: {dtype} (type: {type(dtype)})")


def get_database_data_type(
    platform_type: PlatformType, dtype, max_length: int | None = None
) -> str:
    """Convert data type to database-specific type using standardized DataTypeEnum.

    Args:
        platform_type: Database platform type
        dtype: Data type (can be DataTypeEnum, numpy type, python type, or string)
        max_length: Maximum length for string types

    Returns:
        Database-specific data type string
    """
    platform_key = (
        platform_type.name if hasattr(platform_type, "name") else str(platform_type)
    )

    if platform_key not in _DATATYPE_TO_DATABASE_MAPPING:
        raise ValueError(f"Unsupported platform type: {platform_type}")

    # Normalize the dtype to our standard enum
    try:
        normalized_dtype = _normalize_dtype_key(dtype)
    except ValueError as e:
        raise ValueError(f"Cannot normalize data type '{dtype}': {e}") from e

    dtype_key = (
        normalized_dtype.name
        if hasattr(normalized_dtype, "name")
        else str(normalized_dtype)
    )

    if dtype_key not in _DATATYPE_TO_DATABASE_MAPPING[platform_key]:
        raise ValueError(
            f"Unsupported data type '{dtype}' (normalized: '{normalized_dtype}') for platform {platform_type}"
        )

    type_mapper = _DATATYPE_TO_DATABASE_MAPPING[platform_key][dtype_key]
    if callable(type_mapper):
        return str(type_mapper(max_length))
    return str(type_mapper)


def get_datatype_from_database(
    platform_type: PlatformType, database_type: str
) -> DataTypeEnum:
    """Convert database-specific type back to standardized DataTypeEnum.

    Args:
        platform_type: Database platform type
        database_type: Native database data type string (e.g., 'VARCHAR', 'BIGINT', 'TIMESTAMP')

    Returns:
        Corresponding DataTypeEnum value
    """

    platform_key = (
        platform_type.name if hasattr(platform_type, "name") else str(platform_type)
    )

    if platform_key not in _DATABASE_TO_DATATYPE_MAPPING:
        raise ValueError(f"Unsupported platform type: {platform_type}")

    # Normalize database type to uppercase and remove common suffixes/prefixes
    normalized_db_type = database_type.upper().strip()

    # Handle parameterized types like VARCHAR(255), DECIMAL(10,2), etc.
    if "(" in normalized_db_type:
        normalized_db_type = normalized_db_type.split("(")[0]

    # Handle array types like ARRAY<STRING>
    if normalized_db_type.startswith("ARRAY<") or normalized_db_type.startswith(
        "ARRAY "
    ):
        normalized_db_type = "ARRAY"
    elif normalized_db_type.startswith("MAP<") or normalized_db_type.startswith("MAP "):
        normalized_db_type = "MAP"

    if normalized_db_type not in _DATABASE_TO_DATATYPE_MAPPING[platform_key]:
        raise ValueError(
            f"Unsupported database type '{database_type}' (normalized: '{normalized_db_type}') for platform {platform_type}"
        )

    enum_name = _DATABASE_TO_DATATYPE_MAPPING[platform_key][normalized_db_type]
    return getattr(DataTypeEnum, enum_name)


def convert_database_schema_to_datatypes(
    platform_type: PlatformType, schema_dict: dict[str, str]
) -> dict[str, "DataTypeEnum"]:
    """Convert a database schema dictionary to standardized DataTypeEnum values.

    This is useful for schema introspection where you get column definitions from
    a database and want to convert them to standardized types.

    Args:
        platform_type: Database platform type
        schema_dict: Dictionary mapping column names to database-specific types

    Returns:
        Dictionary mapping column names to DataTypeEnum values
    """
    return {
        column_name: get_datatype_from_database(platform_type, db_type)
        for column_name, db_type in schema_dict.items()
    }


def get_pandas_dtype_from_enum(data_type_enum: DataTypeEnum):
    """Convert DataTypeEnum to pandas/numpy compatible dtype.

    This provides the reverse operation of _normalize_dtype_key(), allowing you to
    convert from DataTypeEnum back to pandas dtypes for DataFrame operations.

    NOTE: Uses pandas nullable types (Int64, string, boolean) to properly handle
    NA/blank values in CSV files and databases. This prevents errors when reading
    data with missing values in integer or string columns.

    Args:
        data_type_enum: The DataTypeEnum value to convert

    Returns:
        Pandas-compatible dtype (numpy type or string)

    Examples:
        >>> get_pandas_dtype_from_enum(DataTypeEnum.STRING)
        'string'  # Pandas nullable string
        >>> get_pandas_dtype_from_enum(DataTypeEnum.INT64)
        'Int64'  # Pandas nullable Int64 (handles NA values)
        >>> get_pandas_dtype_from_enum(DataTypeEnum.BOOLEAN)
        'boolean'  # Pandas nullable boolean
    """
    if data_type_enum not in _DATATYPE_TO_PANDAS_MAPPING:
        raise ValueError(f"Unsupported DataTypeEnum: {data_type_enum}")

    return _DATATYPE_TO_PANDAS_MAPPING[data_type_enum]


def convert_datatypes_to_pandas_schema(
    schema_dict: dict[str, DataTypeEnum],
) -> dict[str, Any]:
    """Convert a schema dictionary of DataTypeEnum values to pandas dtypes.

    This is useful when you have a standardized schema and want to apply it to
    a pandas DataFrame (e.g., when reading CSV files with pd.read_csv(dtype=...)).

    Args:
        schema_dict: Dictionary mapping column names to DataTypeEnum values

    Returns:
        Dictionary mapping column names to pandas-compatible dtypes

    Examples:
        >>> schema = {
        ...     'id': DataTypeEnum.INT64,
        ...     'name': DataTypeEnum.STRING,
        ...     'active': DataTypeEnum.BOOLEAN
        ... }
        >>> convert_datatypes_to_pandas_schema(schema)
        {'id': numpy.int64, 'name': 'object', 'active': numpy.bool_}
    """
    return {
        column_name: get_pandas_dtype_from_enum(dtype)
        for column_name, dtype in schema_dict.items()
    }
