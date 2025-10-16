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
"""Database Interface/Abstract Client."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, fields
from typing import Any, Iterable, List, Optional, Sequence, Type

from pandas import DataFrame as PandaDataFrame

from ..clgxtyping import PlatformType
from ..error_codes import CommonErrorCodes
from ..exception import ClgxException
from .database_types import ColumnDefinition, get_database_data_type


@dataclass(frozen=False)
class DbConfig:
    """Database configuration.

    Args:
        string_quotation: Quotation marks for string literals
        table_name_seperator: Separator for table names
        table_quotation: Prefix for table names

    """

    db_type: PlatformType = PlatformType.SNOWFLAKE
    string_quotation: str = '"'
    table_name_seperator: str = "."
    table_quotation: str = ""
    inside_native_platform: bool = True


# ====== DB Abstract/Interface Client
class DatabaseClient(ABC):
    """Abstract DbClient.

    Args:
        ABC (_type_): Abstract Class
    """

    def __init__(self, config: DbConfig) -> None:
        """Initialize the database client.

        Args:
            config (DbConfig): Database Configuration
        """
        self.__config = config

    # ========== Metadata
    @abstractmethod
    def get_session_info(self) -> dict[str, str]:
        """Return session information as a dictionary.

        Returns:
            dict[str, str]: Dictionary with session information.
        """

    @abstractmethod
    def get_databases(self) -> list[str]:
        """Return list of database names.

        Returns:
            List[str]: List of database names.
        """

    @abstractmethod
    def get_default_database(self) -> str:
        """Return the default database name.

        Returns:
            str: Default database name.
        """

    @abstractmethod
    def get_schemas(self, database: str) -> list[str]:
        """Return list of schema names for a given database.

        Args:
            database (str): Database name

        Returns:
            List[str]: List of schema names.
        """

    def parse_table(self, table: str) -> tuple[str, str, str]:
        """Parse table name to database, schema & table name.
        This is used to get the database and schema name from the table name.
        Override this method if the database platform is different
        Args:
            table (str): Full table name

        Returns:
            tuple[str, str, str]: Tuple of database, schema and table name
        """
        # remove table quotation if exists
        table = self.remove_table_quotation(table)
        tokens = table.split(self.__config.table_name_seperator)
        if len(tokens) >= 3:
            database = tokens[0]
            schema = tokens[1]
            table = tokens[2]
        elif len(tokens) == 2:
            database = ""
            schema = tokens[0]
            table = tokens[1]
        else:
            database = ""
            schema = ""
            table = tokens[0]
        return database, schema, table

    def full_table_name(
        self,
        database: str,
        schema: str,
        table: str,
        include_table_quotation: bool = True,
    ) -> str:
        """Return full table name with database and schema.

        Args:
            database (str): Database name
            schema (str): Schema name
            table (str): Table name
            include_table_quotation (bool): Whether to include table name quotation.
            Bigquery table name must be enclosed in backticks.

        Returns:
            str: Full table name
        """
        full_table_name = ""
        if database:
            full_table_name += f"{database}{self.__config.table_name_seperator}"
        if schema:
            full_table_name += f"{schema}{self.__config.table_name_seperator}"

        return (
            f"{self.__config.table_quotation}{full_table_name}{table}{self.__config.table_quotation}"
            if include_table_quotation
            else f"{full_table_name}{table}"
        )

    def remove_table_quotation(self, table: str) -> str:
        """Remove table name quotation.

        Args:
            table (str): Full table name

        Returns:
            str: Table name without quotation
        """
        return table.replace(self.__config.table_quotation, "")

    @property
    def config(self) -> DbConfig:
        """Return database configuration.

        Args:
            None
        Returns:
            DbConfig: Database configuration
        """
        return self.__config

    @abstractmethod
    def get_tables(self, database: str, schema: str) -> list[str]:
        """Return list of table names from the database and schema

        Args:
            database (str): Database name
            schema (str): Schema name.

        Returns:
            List[str]: List of table names
        """

    @abstractmethod
    def get_column_names(self, table: str) -> list[str]:
        """Return list of column names.

        Args:
             table (str): Full table ID in format `project.dataset.table`.

        Returns:
            List[str]: List of column names.
        """

    @abstractmethod
    def get_column_data_types(self, table: str) -> dict[str, str]:
        """Return dictionary of column names with datatypes

        Args:
             table (str): Full table ID in format `project.dataset.table`.

        Returns:
            Dict[str,str]: dict of column names with dtypes
        """

    def table_exists(self, table: str) -> bool:
        """Check if table exists in database.

        Args:
            table (str): Full table name

        Returns:
            bool: True or False
        """
        database, schema, table_name_only = self.parse_table(table)
        tables = self.get_tables(database, schema)
        return bool(not tables and len(tables) > 0 and table_name_only in tables)

    def create_temporary_table_keyword(self) -> str:
        """Return keyword to create temporary table.

        Returns:
            str: Keyword to create temporary table
        """
        return "TEMPORARY"

    def clean_text_format(self, column_name: str) -> str:
        """Generate cross-platform SQL for text cleaning.

        Args:
            column_name (str): Column name to clean

        Returns:
            str: Cross-platform SQL expression for text cleaning
        """
        # Build regex pattern to avoid Python escape sequence issues
        # allowed_chars = "0-9a-zA-Z \\_\\&\\+.,#\\'\\/"
        # backslash = "\\\\\\\\"  # Four backslashes for one literal backslash in SQL
        # regex_pattern = f"[^{allowed_chars}{backslash}]"
        regex_pattern = "[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]"  # Control characters

        return f"""
TRIM(
    REGEXP_REPLACE(
        REGEXP_REPLACE(input.{column_name}, '{regex_pattern}', ''),
        '\\\\s+', ' '
    )
)""".strip()

    # ================== Table Operations
    def create_table(
        self,
        column_definitions: List[ColumnDefinition],
        table: str,
        if_not_exists: bool = True,
        app_role: Optional[str] = None,
    ) -> None:
        """Create table with the specified schema.

        Args:
            column_definitions (List[ColumnDefinition]): List of column definitions
            table (str): Full table name
            if_not_exists (bool, optional): Create table if not exists. Defaults to True.
            app_role (Optional[str], optional): Grant permission to application role. Defaults to None. This only applies to Snowflake

        Raises:
            ValueError: If column_definitions is empty or contains invalid definitions
        """
        if not column_definitions:
            raise ValueError("Cannot create table without column definitions")
        column_sql_definitions = []
        primary_keys = []
        for column_def in column_definitions:
            # Use the native column name directly
            column_name = column_def.name
            data_type = get_database_data_type(
                self.__config.db_type, column_def.data_type, column_def.max_length
            )

            # Build column definition
            col_sql = f"{column_name} {data_type}"

            # Add NOT NULL constraint
            if not column_def.nullable:
                col_sql += " NOT NULL"

            # Default value if not supported by all database during table creation.
            # Set the default values during insert/update operations instead.
            column_sql_definitions.append(col_sql)

            # Track primary keys
            if column_def.primary_key:
                primary_keys.append(column_name)

        # Build the full SQL
        if_not_exist = " IF NOT EXISTS " if if_not_exists else " "
        sql_parts = [f"CREATE TABLE{if_not_exist}{table} ("]
        sql_parts.extend(column_sql_definitions)

        # Add primary key constraint for platforms that support it
        if primary_keys and self.__config.db_type in [
            PlatformType.SNOWFLAKE,
            PlatformType.DATABRICKS,
        ]:
            pk_constraint = f"    PRIMARY KEY ({', '.join(primary_keys)})"
            sql_parts.append(pk_constraint)

        sql_parts.append(")")

        if self.__config.db_type == PlatformType.BIGQUERY and primary_keys:
            pk_constraint = f"CLUSTER BY {','.join(primary_keys)}"
            sql_parts.append(pk_constraint)

        # Join columns with commas for proper SQL formatting
        opening_line = sql_parts[0]
        column_lines = sql_parts[1:-1]  # All middle parts (columns and constraints)
        closing_line = sql_parts[-1]

        if column_lines:
            # Format with proper indentation: each column/constraint on its own line
            formatted_columns = [f"    {line}" for line in column_lines]
            sql = (
                opening_line
                + "\n"
                + ",\n".join(formatted_columns)
                + "\n"
                + closing_line
            )
        else:
            # Empty table (shouldn't happen due to validation, but safety)
            sql = opening_line + "\n" + closing_line

        self.execute(sql)

        if (
            app_role
            and self.__config.db_type == PlatformType.SNOWFLAKE
            and self.__config.inside_native_platform
        ):
            grant_sql = f"GRANT ALL ON TABLE {table} TO APPLICATION ROLE {app_role};"
            self.execute(grant_sql)

    def get_non_unique_row_counts(self, table: str, column: str) -> int:
        """Return non-unique row counts of the column in the table.

        Args:
            table (str): Table name
            column (str): Column name to check for non-unique values

        Returns:
            int: Non-unique row counts
        """
        sql = f"SELECT COUNT({column}) - COUNT(DISTINCT {column}) AS non_unique_count FROM {table}"
        df = self.query_to_pandas(sql)
        if df.empty or "non_unique_count" not in df.columns:
            return 0
        return int(df["non_unique_count"].iloc[0])

    @abstractmethod
    def row_counts(self, table: str) -> int:
        """Return row counts of the table.

        Args:
            table (str): Table name
        Returns:
            int: Row counts
        """

    @abstractmethod
    def row_counts_for_tables(
        self, database: str, schema: str, table_filters: Optional[List[str]] = None
    ) -> dict[str, int]:
        """Return row counts of all tables in the database and schema.

        Args:
            database (str): Database name
            schema (str): Schema name
            table_filters (Optional[List[str]], optional): List of table names to filter. Defaults to None.

        Returns:
            dict[str, int]: Dictionary with table names as keys and row counts as values.
        """

    def table_name_quotation(self, table: str) -> str:
        """Return table name with quotaion.
            Override this method if the database platform is different
        Args:
            table (str): Table name

        Returns:
            str: Quoted table name
        """
        return table

    @abstractmethod
    def clone_table(
        self, source_table: str, destination_table: str, copy_data: bool = False
    ) -> None:
        """Create table with the specified schema.

        Args:
            source_table (str): Source table name
            destination_table (str): Destination table name
            copy_data (bool, optional): Copy data from source to destination. Defaults to False.
        """

    @abstractmethod
    def drop_table(self, table: str) -> None:
        """Drop this table.

        Args:
            table (str): Table name
        """

    @abstractmethod
    def truncate_table(self, table: str) -> None:
        """Truncate this table.

        Args:
            table (str): Table name
        """

    @abstractmethod
    def cast_to_string(self, column: str) -> str:
        """Return SQL to cast the column to string.

        Args:
            column (str): Column name

        Returns:
            str: SQL to cast the column to string
        """

    # ================== Execute SQL
    @abstractmethod
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        """Execute SQL statement.
        Args:
            sql (str): SQL statement
            params (Optional[Sequence[Any]], optional): Parameters for the SQL query. Defaults to None.
        Returns:
            None
        """

    @abstractmethod
    def call_proc(self, proc_name: str, *args):
        """Call stored procedure with arguments.

        Args:
            proc_name (str): Procedure name
            *args: Arguments for the procedure
        Returns:
            None
        """

    # ================== Write Data
    @abstractmethod
    def append_data(self, dataframe: PandaDataFrame, table: str) -> None:
        """Append data to the destination table.

        Args:
            table (str): Table name
            dataframe (PandaDataFrame): Dataframe to append
        Returns:
            None
        """

    # ================== Query Data
    @abstractmethod
    def table_to_pandas(
        self, table: str, columns: list[str] | None = None, limit: int = 0
    ) -> PandaDataFrame:
        """Query and return all records to Panda dataframe.

        Args:
            table (str): Table name
            columns (list[str] | None, optional): List of columns to select. Defaults to None (select all).
            limit (int, optional): Limit the number of records. Defaults to 0 (no limit).
        Returns:
            PandaDataFrame: Dataframe with records.
        """

    @abstractmethod
    def query_to_pandas(
        self, query_sql: str, params: Optional[Sequence[Any]] = None
    ) -> PandaDataFrame:
        """Query and return all records to Panda dataframe.

        Args:
            query_sql (str): SQL
            params (Optional[Sequence[Any]], optional): Parameters for the SQL query. Defaults to None.
        Returns:
            PandaDataFrame: Dataframe with records.
        """

    @abstractmethod
    def query_to_pandas_interator(
        self,
        query_sql: str,
        page_size: int = 1000,
        params: Optional[Sequence[Any]] = None,
    ) -> Iterable[PandaDataFrame]:
        """Return Panda Iterator to fetch records from this query.

        Args:
            query_sql (str): SQL
            page_size (int, optional): Page size. Defaults to 100.
            params (Optional[Sequence[Any]], optional): Parameters for the SQL query. Defaults to None.
        Returns:
            Iterable[PandaDataFrame]: Iterable of Panda DataFrames with records.
        """

    @abstractmethod
    def query_to_dict(
        self, query_sql: str, params: Optional[Sequence[Any]] = None
    ) -> List[dict]:
        """Query and return all records to List[dict].

        Args:
            query_sql (str): SQL
            params (Optional[Sequence[Any]], optional): Parameters for the SQL query. Defaults to None.
        Returns:
            List[dict]: List of dictionaries with records.
        """


# Re-export the database type mapping functions from database_types module
# Import moved to top of file for PEP 8 compliance
