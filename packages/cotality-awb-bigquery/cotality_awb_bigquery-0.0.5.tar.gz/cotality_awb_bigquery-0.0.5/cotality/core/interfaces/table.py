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

import enum
import json
from dataclasses import asdict, fields, is_dataclass
from typing import (
    Any,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import pandas as pd

from ...core.error_codes import CommonErrorCodes
from ...core.exception import ClgxException
from .database import DatabaseClient
from .database_types import ColumnDefinition, DataTypeEnum

# Generic type for ORM operations - constrained to dataclass instances
T = TypeVar("T")


class Table(Generic[T]):
    """Generic table definition for database table operations.

    This class provides a clean, type-safe way to define tables
    with all necessary metadata for SQL generation and ORM operations.

    Type parameter T represents the dataclass type associated with this table.

    ## 🏗️ Design Rationale: Custom ORM vs Open Source Alternatives

    This custom ORM implementation was chosen over established open source ORMs
    (like SQLAlchemy, Peewee, or Django ORM) for several critical reasons:

    ### 1. **Dependency Minimization** (Primary Driver)
    - **Snowflake Native Apps**: Snowflake native applications have strict limitations
      on external dependencies and only allow pre-approved packages
    - **Enterprise Security**: Reduces attack surface by minimizing third-party code
    - **Supply Chain Security**: Avoids dependency vulnerabilities from external packages
    - **Version Control**: No conflicts with different ORM versions across environments

    ### 2. **Lightweight & Performance**
    - **Minimal Overhead**: Direct SQL generation without heavy abstraction layers
    - **Fast Startup**: No complex ORM initialization or metadata reflection
    - **Memory Efficient**: Simple dataclass-based models with minimal memory footprint
    - **Query Performance**: Predictable SQL generation with no hidden N+1 queries

    ### 3. **Platform Integration**
    - **Multi-Database Support**: Native integration with Snowflake, BigQuery, and other platforms
    - **Type Safety**: Full type hints and Generic support for compile-time checking
    - **JSON Serialization**: Built-in DataClassJsonMixin integration for complex fields
    - **Business Logic**: Seamless integration with Cotality's business domain models

    ### 4. **Simplicity & Maintainability**
    - **Clear Intent**: Explicit table definitions with ColumnDefinition schemas
    - **Predictable Behavior**: No magic methods or complex metaclass hierarchies
    - **Easy Debugging**: Direct SQL visibility and straightforward error handling
    - **Team Productivity**: Minimal learning curve for developers familiar with dataclasses

    ### 5. **Enterprise Requirements**
    - **Audit Trail**: Full control over SQL generation for compliance requirements
    - **Security**: No ORM-level SQL injection vulnerabilities from complex query builders
    - **Customization**: Easy extension for enterprise-specific database features
    - **Documentation**: Self-documenting code with clear business context

    This approach provides the essential ORM functionality needed while maintaining
    the flexibility, security, and dependency constraints required for enterprise
    deployment, particularly in restricted environments like Snowflake native applications.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        dataclass_type: Type[T],
        database_name: str,
        schema_name: str,
        table_name: str,
        columns: List[ColumnDefinition],
        description: str = "",
        app_role: str = "",
    ):
        """Initialize Table with associated dataclass type.

        Args:
            database_client (DatabaseClient): Database client instance
            dataclass_type (Type[T]): The dataclass type associated with this table
            database_name (str): Database name
            schema_name (str): Schema name
            table_name (str): Table name
            columns (List[ColumnDefinition]): List of column definitions
            description (str, optional): Table description. Defaults to "".
            app_role (str, optional): Application role for permissions (Snowflake only). Defaults to "".
        """
        self._database_client = database_client
        self._dataclass_type = dataclass_type
        self._database_name = database_name
        self._schema_name = schema_name
        self._table_name = database_client.full_table_name(
            database_name, schema_name, table_name
        )
        self._columns = columns
        self._description = description
        self._app_role = app_role
        self._primary_keys = [col for col in columns if col.primary_key]
        if not self._primary_keys:
            raise ClgxException(
                error=CommonErrorCodes.DB_MISSING_PRIMARY_KEYS,
                parameters={
                    "name": f"Model:{self._dataclass_type.__name__}, Table:{self._table_name}"
                },
            )
        self._non_primary_keys = [col for col in columns if not col.primary_key]
        self._alias_to_column_names = {
            col.alias: col.name for col in self._columns if col.alias
        }
        self._alias_to_columns = {col.alias: col for col in self._columns if col.alias}

    # ===== Property Functions =====

    @property
    def database_client(self) -> DatabaseClient:
        """Return the associated DatabaseClient instance.

        Returns:
            DatabaseClient: The database client used for this table
        """
        return self._database_client

    @property
    def database_name(self) -> str:
        """Return database name.

        Returns:
            str: Database name
        """
        return self._database_name

    @property
    def schema_name(self) -> str:
        """Return schema name.

        Returns:
            str: Schema name
        """
        return self._schema_name

    @property
    def table_name(self) -> str:
        """Return table name.

        Returns:
            str: Table name
        """
        return self._table_name

    def get_tables(self) -> list[str]:
        """Return list of table names from the database and schema

        Args:
            database (str): Database name
            schema (str): Schema name.

        Returns:
            List[str]: List of table names
        """
        return self._database_client.get_tables(
            database=self.database_name, schema=self.schema_name
        )

    def get_table_name(self, table_name: Optional[str] = None) -> str:
        """Return table name.

        Returns:
            str: Table name
        """
        if table_name:
            _, _, table_name_only = self._database_client.parse_table(table_name)
            table_name = self._database_client.full_table_name(
                self._database_name, self._schema_name, table_name_only
            )

        return table_name if table_name else self._table_name

    @property
    def dataclass_type(self) -> Type[T]:
        """Return the associated dataclass type.

        Returns:
            Type[T]: The dataclass type associated with this table
        """
        return self._dataclass_type

    # ====== Get columns ======
    @property
    def columns(self) -> Tuple[list[ColumnDefinition], List[ColumnDefinition]]:
        """Return dictionary of column definitions grouped by 'group' attribute.

        Returns:
            Tuple[List[ColumnDefinition], List[ColumnDefinition]]: Tuple of (primary key columns, non-primary key columns)
        """
        return self._primary_keys, self._non_primary_keys

    @property
    def columns_by_group(self) -> dict[str, List[ColumnDefinition]]:
        """Return dictionary of column definitions grouped by 'group' attribute.

        Returns:
            Dict[str, List[ColumnDefinition]]: Dictionary with group names as keys and lists of column definitions as values
        """
        grouped_columns = {}
        for col in self._columns:
            group_name = col.group if col.group else "default"
            if group_name not in grouped_columns:
                grouped_columns[group_name] = []
            grouped_columns[group_name].append(col)
        return grouped_columns

    def get_columns_by_group(
        self, groups: list[str] | str
    ) -> dict[str, List[ColumnDefinition]]:
        """Return list of column definitions for given group(s).

        Args:
            groups (List[str]): List of group names
        Returns:
            Dict[str, List[ColumnDefinition]]: Dictionary with group names as keys and lists of column definitions as values
        """
        if isinstance(groups, str):
            groups = [groups]
        return {g: self.columns_by_group.get(g, []) for g in groups}

    def get_columns_from_aliases(
        self, aliases: List[str] | str
    ) -> List[ColumnDefinition]:
        """Return list of column definitions for given aliases.

        Args:
            aliases (List[str]): List of column aliases
        Returns:
            List[ColumnDefinition]: List of column definitions corresponding to the aliases
        """
        if isinstance(aliases, str):
            aliases = [aliases]
        return [
            self._alias_to_columns[alias]
            for alias in aliases
            if alias in self._alias_to_columns
        ]

    def get_columns_from_aliases_as_dict(
        self, aliases: List[str] | str
    ) -> dict[str, ColumnDefinition]:
        """Return dictionary of column definitions for given aliases.

        Args:
            aliases (List[str]): List of column aliases
        Returns:
            Dict[str, ColumnDefinition]: Dictionary with aliases as keys and column definitions as values
        """
        if isinstance(aliases, str):
            aliases = [aliases]
        return {
            alias: self._alias_to_columns[alias]
            for alias in aliases
            if alias in self._alias_to_columns
        }

    # ====== Get column names ======
    @property
    def column_names(self) -> Tuple[List[str], List[str]]:
        """Return list of column names.

        Returns:
            Tuple[List[str], List[str]]: Tuple of (primary key column names, non-primary key column names)
        """
        primary_keys = [col.name for col in self._columns if col.primary_key]
        non_primary_keys = [col.name for col in self._columns if not col.primary_key]
        return primary_keys, non_primary_keys

    @property
    def column_names_by_group(self) -> dict[str, List[str]]:
        """Return dictionary of column names grouped by 'group' attribute.

        Returns:
            Dict[str, List[str]]: Dictionary with group names as keys and lists of column names as values
        """
        grouped_column_names = {}
        for col in self._columns:
            group_name = col.group if col.group else "default"
            if group_name not in grouped_column_names:
                grouped_column_names[group_name] = []
            grouped_column_names[group_name].append(col.name)
        return grouped_column_names

    def get_colunm_names_by_group(
        self, groups: List[str] | str
    ) -> dict[str, List[str]]:
        """Return list of column names for given group(s).

        Args:
            groups (List[str]): List of group names
        Returns:
            Dict[str, List[str]]: Dictionary with group names as keys and lists of column names as values
        """
        if isinstance(groups, str):
            groups = [groups]
        return {g: self.column_names_by_group.get(g, []) for g in groups}

    def get_column_names_from_aliases(self, aliases: List[str] | str) -> List[str]:
        """Return list of column names for given aliases.

        Args:
            aliases (List[str]): List of column aliases
        Returns:
            List[str]: List of column names corresponding to the aliases
        """
        if isinstance(aliases, str):
            aliases = [aliases]
        return [
            self._alias_to_column_names[alias]
            for alias in aliases
            if alias in self._alias_to_column_names
        ]

    def get_column_names_from_aliases_as_dict(
        self, aliases: List[str] | str
    ) -> dict[str, str]:
        """Return dictionary of column names for given aliases.

        Args:
            aliases (List[str]): List of column aliases
        Returns:
            Dict[str, str]: Dictionary with aliases as keys and column names as values
        """
        if isinstance(aliases, str):
            aliases = [aliases]
        return {
            alias: self._alias_to_column_names[alias]
            for alias in aliases
            if alias in self._alias_to_column_names
        }

    # ====== Row Count Functions ======
    def row_counts(self, table_name: Optional[str] = None) -> int:
        """Return number of rows in the table.
        Args:
            table_name (Optional[str], optional): Table name to check row counts. Defaults to None, which uses the current table.
        Returns:
            int: Number of rows in the table
        """
        table_name = self.get_table_name(table_name)
        return self._database_client.row_counts(table_name)

    def row_counts_for_tables(
        self, table_filters: Optional[List[str]] = None
    ) -> dict[str, int]:
        """Return row counts of all tables in the database and schema.

        Args:
            table_filters (Optional[List[str]], optional): List of table names to filter. Defaults to None.

        Returns:
            dict[str, int]: Dictionary with table names as keys and row counts as values.
        """
        return self._database_client.row_counts_for_tables(
            database=self._database_name,
            schema=self._schema_name,
            table_filters=table_filters,
        )

    @property
    def primary_keys(self) -> List[str]:
        """Return list of primary key columns.

        Returns:
            List[str]: List of primary key column names
        """
        return [col.name for col in self._primary_keys]

    # ===== Simple Get/Set Functions =====

    def alias_to_column(self, alias: str) -> str:
        """Return column name for a given alias.

        Args:
            alias (str): Column alias
        Returns:
            str: Column name corresponding to the alias
        """
        return self._alias_to_column_names.get(alias, "")

    def get_row_counts(
        self,
        conditions: str,
        params: Optional[List[Any]] = None,
        table_name: Optional[str] = None,
    ) -> int:
        """Return number of rows in the table matching the condition.

        Args:
            conditions (str): SQL condition for filtering rows
            params (Optional[List[Any]], optional): Parameters for the query. Defaults to None.
            table_name (Optional[str], optional): Table name to check row counts. Defaults to None, which uses the current table.
        Returns:
            int: Number of rows matching the condition
        """
        table_name = self.get_table_name(table_name)
        sql = f"SELECT COUNT(*) as count FROM {table_name} WHERE {conditions}"
        df = self._database_client.query_to_dict(query_sql=sql, params=params)
        count = 0
        if df and len(df) > 0:
            count = int(df[0].get("count", 0))
        return count

    def get_column_mapping(self, model_fields: List[str]) -> dict[str, str]:
        """Get column mapping from model fields to table columns.

        This method prioritizes matching model field names with column aliases first,
        then falls back to actual column names. This supports business-friendly model
        attributes that correspond to column aliases rather than database column names.

        Args:
            model_fields (List[str]): List of model field names

        Returns:
            dict[str, str]: Mapping from model fields to actual column names
        """
        mapping = {}

        # Create lookup dictionaries for efficient searching
        name_to_column = {col.name: col.name for col in self._columns}

        for field in model_fields:
            # First, try to match with column alias
            if field in self._alias_to_column_names:
                mapping[field] = self._alias_to_column_names[field]
            # Then, try to match with actual column name
            elif field in name_to_column:
                mapping[field] = name_to_column[field]
            # If no match found, skip this field (it won't be included in SQL)

        return mapping

    def get(
        self, primary_key_values: Any | List[Any], table_name: Optional[str] = None
    ) -> List[T] | T | None:
        """Get a single row by primary key values with automatic JSON deserialization.

        Convenience method that builds a WHERE clause using primary key fields
        and delegates to DatabaseClient.select(). Uses the table's associated dataclass type.
        Automatically converts JSON strings back to DataClassJsonMixin objects.

        Args:
            primary_key_values (Any | List[Any]): Primary key value(s). If multiple primary keys exist,
                provide a list with values in the same order as self.primary_keys.
                For single primary key, can pass the value directly.
            table_name (Optional[str], optional): Table name to query. Defaults to None, which uses the current table.

        Returns:
            List[T] | T | None: The dataclass instance(s) matching the primary key values, or None if not found.
                Returns a single instance if one row is found, otherwise returns a list of instances.
                If no rows are found, returns None.

        Raises:
            ValueError: If primary key configuration doesn't match provided values
            ValueError: If multiple rows found for the primary key (data integrity issue)

        Examples:
            # Single primary key
            user = user_table.get("user123")

            # Composite primary key
            order_item = order_item_table.get(["order123", "item456"])
        """
        if not self.primary_keys:
            raise ValueError(
                "Table has no primary key defined. Cannot use get() method."
            )

        table_name = self.get_table_name(table_name)
        # Handle single vs multiple primary key values
        if len(self.primary_keys) == 1:
            if isinstance(primary_key_values, list):
                if len(primary_key_values) != 1:
                    raise ValueError(
                        f"Table has 1 primary key but {len(primary_key_values)} values provided"
                    )
                pk_values = primary_key_values
            else:
                pk_values = [primary_key_values]
        else:
            if not isinstance(primary_key_values, list):
                raise ValueError(
                    f"Table has {len(self.primary_keys)} primary keys but only 1 value provided"
                )
            if len(primary_key_values) != len(self.primary_keys):
                raise ValueError(
                    f"Table has {len(self.primary_keys)} primary keys but {len(primary_key_values)} values provided"
                )
            pk_values = primary_key_values

        # Build WHERE clause for primary key lookup
        where_conditions = []
        for pk_field in self.primary_keys:
            where_conditions.append(f"{pk_field} = ?")

        where_clause = " AND ".join(where_conditions)

        # Execute select with primary key values
        return self.select(
            where_clause=where_clause, params=pk_values, table_name=table_name
        )

    # ===== CRUD Functions (Create, Read, Update, Delete) =====

    def create(
        self, if_not_exists: bool = True, table_name: Optional[str] = None
    ) -> None:
        """Create the table in the database.

        Args:
            if_not_exists (bool, optional): Create table if not exists. Defaults to True.
            table_name (Optional[str], optional): Table name to create. Defaults to None, which uses the current table.
        """
        table_name = self.get_table_name(table_name)
        self._database_client.create_table(
            column_definitions=self._columns,
            table=table_name,
            if_not_exists=if_not_exists,
            app_role=self._app_role,
        )

    def insert(self, models: List[T] | T, table_name: Optional[str] = None) -> None:
        """Insert rows into this table with automatic JSON serialization and optional duplicate checking.

        Convenience method that delegates to DatabaseClient.insert().
        Automatically converts DataClassJsonMixin fields to JSON strings for storage.

        Args:
            models (List[T] | T): List of models to insert or single model
            table_name (Optional[str], optional): Table name to insert into. Defaults to None, which uses the current table.

        Raises:
            ValueError: If if_not_exists=True but no primary keys defined

        Examples:
            # Regular insert (existing behavior)
            user_table.insert(new_user)

            # Insert only if user doesn't exist (using primary key)
            user_table.insert(new_user, if_not_exists=True)

            # Batch insert with duplicate checking
            user_table.insert([user1, user2, user3], if_not_exists=True)
        """
        table_name = self.get_table_name(table_name)
        if not isinstance(models, list):
            models = [models]

        return self._insert(table_name=table_name, models=models)

    def select(
        self,
        where_clause: str = "",
        params: Optional[List[Any]] = None,
        order_by: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> List[T] | T | None:
        """Select rows from this table and map to dataclass models with automatic JSON deserialization.

        Convenience method that delegates to DatabaseClient.select().
        Uses the table's associated dataclass type for mapping.
        Automatically converts JSON strings back to DataClassJsonMixin objects.

        Args:
            where_clause (str, optional): WHERE clause for filtering. Defaults to "" (no filtering).
            params (Optional[List[Any]], optional): Parameters for the query. Defaults to None.
            order_by (Optional[str], optional): ORDER BY clause for sorting. Defaults to None (no sorting).
                Can include column names, ASC/DESC, and multiple columns.
                Examples: "name", "created_at DESC", "name ASC, created_at DESC"
            table_name (Optional[str], optional): Table name to query. Defaults to None, which uses the current table.

        Returns:
            List[T]: List of mapped dataclass instances with deserialized JSON fields.

        Examples:
            # Select all users
            users = user_table.select()

            # Select with filtering
            active_users = user_table.select("status = ?", ["active"])

            # Select with sorting
            users_by_name = user_table.select(order_by="name ASC")

            # Select with filtering and sorting
            recent_active_users = user_table.select(
                "status = ? AND created_at > ?",
                ["active", timestamp],
                order_by="created_at DESC"
            )

            # Multiple column sorting
            users_sorted = user_table.select(order_by="status ASC, created_at DESC")
        """
        table_name = self.get_table_name(table_name)
        return self._select(
            table_name=table_name,
            where_clause=where_clause,
            params=params,
            order_by=order_by,
        )

    def update(self, models: List[T] | T, table_name: Optional[str] = None) -> None:
        """Update rows in this table using primary key or specified fields with automatic JSON serialization.

        Convenience method that delegates to DatabaseClient.update().
        Automatically uses primary key fields if where_fields is not specified.
        Handles both single and composite primary keys seamlessly.
        Automatically converts DataClassJsonMixin fields to JSON strings for storage.

        Args:
            models (List[T] | T): List of models to update or single model
            where_fields (Optional[List[str]], optional): Fields to use in WHERE clause.
                If None, uses primary key fields from this Table. If table has no primary key,
                raises ValueError.
            table_name (Optional[str], optional): Table name to update. Defaults to None, which uses the current table.

        Raises:
            ValueError: If where_fields is None and table has no primary key defined

        Examples:
            # Update using single primary key (automatic)
            user.status = "active"
            user_table.update(user)

            # Update using composite primary key (automatic)
            user_role.permissions = "read,write"  # Table has (user_id, role_id) as composite PK
            user_roles_table.update(user_role)  # Uses both user_id AND role_id in WHERE

            # Update using custom where fields
            user_table.update(user, where_fields=["email"])

            # Batch update multiple records
            user_table.update([user1, user2, user3])  # Each uses its own PK values
        """
        table_name = self.get_table_name(table_name)
        return self._update(table_name, models)

    def delete_by_key(
        self, primary_key_values: Any | List[Any], table_name: Optional[str] = None
    ) -> int:
        """Delete rows by primary key values.

        Args:
            primary_key_values (Any | List[Any]): Primary key value(s). If multiple primary keys exist,
                provide a list with values in the same order as self.primary_keys.
                For single primary key, can pass the value directly.
            table_name (Optional[str], optional): Table name to delete from. Defaults to None, which uses the current table.

        Returns:
            int: Number of rows deleted

        Raises:
            ValueError: If primary key configuration doesn't match provided values

        Examples:
            # Single primary key
            deleted_count = user_table.delete_by_key("user123")

            # Composite primary key
            deleted_count = user_roles_table.delete_by_key(["user123", "admin"])
        """
        table_name = self.get_table_name(table_name)
        if not self.primary_keys:
            raise ValueError(
                "Table has no primary key defined. Cannot use delete_by_key() method."
            )

        # Handle single vs multiple primary key values (same logic as get method)
        if len(self.primary_keys) == 1:
            if isinstance(primary_key_values, list):
                if len(primary_key_values) != 1:
                    raise ValueError(
                        f"Table has 1 primary key but {len(primary_key_values)} values provided"
                    )
                pk_values = primary_key_values
            else:
                pk_values = [primary_key_values]
        else:
            if not isinstance(primary_key_values, list):
                raise ValueError(
                    f"Table has {len(self.primary_keys)} primary keys but only 1 value provided"
                )
            if len(primary_key_values) != len(self.primary_keys):
                raise ValueError(
                    f"Table has {len(self.primary_keys)} primary keys but {len(primary_key_values)} values provided"
                )
            pk_values = primary_key_values

        # Build WHERE clause for primary key lookup
        where_conditions = []
        for pk_field in self.primary_keys:
            where_conditions.append(f"{pk_field} = ?")

        where_clause = " AND ".join(where_conditions)

        # Execute DELETE
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        result = self._database_client.execute(sql, pk_values)

        # Return number of affected rows (implementation may vary by database)
        return getattr(result, "rowcount", 1) if result else 0

    def drop(self, table_name: Optional[str] = None) -> None:
        """Drop the table from the database.

        Args:
            if_exists (bool, optional): Drop table if exists. Defaults to True.
            table_name (Optional[str], optional): Table name to drop. Defaults to None, which uses the current table.
        """
        table_name = self.get_table_name(table_name)
        self._database_client.drop_table(table=table_name)

    def truncate_table(self, table_name: Optional[str] = None) -> None:
        """Truncate this table.

        Args:
            table_name (Optional[str], optional): Table name to truncate. Defaults to None, which uses the current table.
        """
        table_name = self.get_table_name(table_name)
        self._database_client.truncate_table(table=table_name)

    def append_data(
        self, dataframe: pd.DataFrame, table_name: Optional[str] = None
    ) -> None:
        """Append data to the destination table.

        Args:
            dataframe (pd.DataFrame): Dataframe to append
            table_name (Optional[str], optional): Table name to append data to. Defaults to None, which uses the current table.
        Returns:
            None
        """
        table_name = self.get_table_name(table_name)
        self._database_client.append_data(dataframe, table_name)

    def table_to_pandas(
        self,
        table_name: Optional[str] = None,
        columns: list[str] | None = None,
        limit: int = 0,
    ) -> pd.DataFrame:
        """Query and return all records to Panda dataframe.

        Args:
            table_name (Optional[str], optional): Table name to query. Defaults to None, which uses the current table.
            columns (list[str] | None, optional): List of columns to select. Defaults to None (select all).
            limit (int, optional): Limit the number of records. Defaults to 0 (no limit).
        Returns:
            pd.DataFrame: Dataframe with records.
        """
        table_name = self.get_table_name(table_name)
        return self._database_client.table_to_pandas(table_name, columns, limit)

    # ===== Private Methods =====
    # All private variables and methods are organized at the end of the class for better code structure

    # ===== ORM Mappings =====
    def _insert(self, table_name: str, models: List[T] | T) -> None:
        """Insert multiple rows into the table.

        Args:
            table_name (str): Name of the table to insert into
            models (List[T] | T): List of models to insert or single model
        """

        if not isinstance(models, list):
            models = [models]

        if not models:
            return

        columns = []
        rows = []
        is_column_name_initialized = False
        for model in models:
            row = []
            for field in fields(model):  # type: ignore
                if not is_column_name_initialized:
                    columns.append(field.name)
                value = getattr(model, field.name)
                if is_dataclass(value) and not isinstance(value, type):
                    value = json.dumps(asdict(value))
                elif isinstance(value, enum.Enum):
                    value = value.value
                row.append(value)
            is_column_name_initialized = True
            rows.append(row)

        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        # Execute for each row
        for row in rows:
            self._database_client.execute(sql, row)

    def _update(
        self,
        table_name: str,
        models: List[T] | T,
    ) -> None:
        """Update multiple rows in the table.

        Args:
            table_name (str): Name of the table to update
            models (List[T] | T): List of models to update or single model
        """
        if not isinstance(models, list):
            models = [models]

        if not models:
            return

        # Get primary key field names for WHERE clause
        primary_key_fields = [col.name for col in self._primary_keys]

        # Build column lists for SET and WHERE clauses
        set_column_names = []
        where_column_names = []

        # Initialize column names based on first model
        first_model = models[0]
        for field in fields(first_model):  # type: ignore
            if field.name in primary_key_fields:
                where_column_names.append(field.name)
            else:
                set_column_names.append(field.name)

        # Process each model
        set_rows = []
        where_rows = []

        for model in models:
            set_values = []
            where_values = []

            for field in fields(model):  # type: ignore
                value = getattr(model, field.name)
                if is_dataclass(value) and not isinstance(value, type):
                    value = json.dumps(asdict(value))
                elif isinstance(value, enum.Enum):
                    value = value.value

                if field.name in primary_key_fields:
                    where_values.append(value)
                else:
                    set_values.append(value)

            set_rows.append(set_values)
            where_rows.append(where_values)

        # Build UPDATE SQL with correct syntax
        set_clause = ", ".join([f"{col} = ?" for col in set_column_names])
        where_clause = " AND ".join([f"{col} = ?" for col in where_column_names])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        # Execute for each model
        for idx, set_values in enumerate(set_rows):
            self._database_client.execute(sql, set_values + where_rows[idx])

    def _select(
        self,
        table_name: str,
        where_clause: str = "",
        params: Optional[List[Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[T] | T | None:
        """Select rows from the table and map to dataclass models.

        Args:
            dataclass_type (Type[T]): Dataclass type to map the results to
            table (Table | str): Table definition with column mappings, or table name for backwards compatibility
            where_clause (str, optional): WHERE clause for filtering. Defaults to "" (no filtering).
            params (Optional[List[Any]], optional): Parameters for the query. Defaults to None.
            order_by (Optional[str], optional): ORDER BY clause for sorting. Defaults to None (no sorting).
                Can include column names, ASC/DESC, and multiple columns.
                Examples: "name", "created_at DESC", "name ASC, created_at DESC"

        Returns:
            List[T]: List of mapped dataclass instances.
        """
        # Get field names from dataclass
        model_fields = self._get_model_fields(self.dataclass_type)
        column_mapping = self.get_column_mapping(model_fields)

        # Apply column mapping if provided
        if column_mapping:
            columns = [column_mapping.get(field, field) for field in model_fields]
        else:
            columns = model_fields

        # Build SELECT SQL
        columns_str = ", ".join(columns)
        sql = f"SELECT {columns_str} FROM {table_name}"
        if where_clause.strip():
            sql += f" WHERE {where_clause}"
        if order_by and order_by.strip():
            sql += f" ORDER BY {order_by}"

        # Execute query and get results
        results = self._database_client.query_to_dict(sql, params)

        # Convert results to dataclass instances
        instances = []
        for row in results:
            instances.append(self._dataclass_type(**row))

        if len(instances) == 1:
            return instances[0]
        if len(instances) == 0:
            return None
        return instances

    # ===== Private Helper Methods =====
    # All private variables and methods are organized at the end of the class for better code structure

    def _get_model_fields(self, model_or_type: Any) -> List[str]:
        """Get field names from a dataclass instance or type."""
        try:
            return [f.name for f in fields(model_or_type)]
        except Exception as e:
            # Fallback for non-dataclass types
            if hasattr(model_or_type, "__dataclass_fields__"):
                return list(model_or_type.__dataclass_fields__.keys())
            raise ClgxException(
                error=CommonErrorCodes.GEN_INVALID_PARAMETER,
                parameters={"name": "model_or_type"},
                message=f"Expected dataclass instance, got {type(model_or_type)}",
                cause=e,
            ) from e

    def _model_to_dict(self, model: Any) -> dict:
        """Convert a dataclass instance to dictionary."""
        try:
            return asdict(model)
        except Exception as e:
            # Fallback for non-dataclass types
            if hasattr(model, "__dataclass_fields__"):
                return {
                    field: getattr(model, field) for field in model.__dataclass_fields__
                }
            raise ClgxException(
                error=CommonErrorCodes.GEN_INVALID_PARAMETER,
                parameters={"name": "model"},
                message=f"Expected dataclass instance, got {type(model)}",
                cause=e,
            ) from e


def separate_primary_and_non_primary_columns(
    column_definitions: List[ColumnDefinition],
) -> Tuple[List[ColumnDefinition], List[ColumnDefinition]]:
    """Separate column definitions into primary key and non-primary key lists.

    This function takes a list of ColumnDefinition objects and separates them into
    two lists while preserving the original order within each list.

    Args:
        column_definitions: List of ColumnDefinition objects to separate

    Returns:
        Tuple containing:
        - First list: All primary key columns in their original order
        - Second list: All non-primary key columns in their original order

    Example:
        >>> cols = [
        ...     ColumnDefinition("id", DataTypeEnum.INT64, primary_key=True),
        ...     ColumnDefinition("name", DataTypeEnum.STRING),
        ...     ColumnDefinition("created_at", DataTypeEnum.TIMESTAMP),
        ...     ColumnDefinition("user_id", DataTypeEnum.INT64, primary_key=True)
        ... ]
        >>> primary, non_primary = separate_primary_and_non_primary_columns(cols)
        >>> [col.name for col in primary]
        ['id', 'user_id']
        >>> [col.name for col in non_primary]
        ['name', 'created_at']
    """
    primary_columns = []
    non_primary_columns = []

    for column_def in column_definitions:
        if column_def.primary_key:
            primary_columns.append(column_def)
        else:
            non_primary_columns.append(column_def)

    return primary_columns, non_primary_columns
