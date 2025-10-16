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
"""BigQuery Database client"""
from __future__ import annotations

import logging
from typing import Any, Iterable, List, Optional, Sequence

from google.cloud import bigquery
from pandas import DataFrame as PandaDataFrame

from ...core.clgxtyping import PlatformType
from ...core.exception import ClgxException, CommonErrorCodes
from ...core.interfaces.database import DatabaseClient as DatabaseInterface
from ...core.interfaces.database import DbConfig
from ...core.logger import (
    LOG_HEADER_KEY_DATABASE,
    LOG_HEADER_KEY_SERVER,
    set_log_header,
)

logger = logging.getLogger(__name__)

# BigQuery uses backticks for quoting identifiers
db_config = DbConfig(
    db_type=PlatformType.BIGQUERY,
    string_quotation='"',
    table_name_seperator=".",
    table_quotation="`",
)


class PandaBqQueryIterator:
    """PandaBqQueryIterator."""

    def __init__(self, query_job: bigquery.QueryJob, page_size: int = 1000):
        """Pandabqqueryiterator initialize method.

        Args:
            query_job (bigquery.QueryJob): BigQuery query job.
            page_size (int, optional): Page size. Defaults to 1000.
        """
        self.__iterator = query_job.result(page_size=page_size).to_dataframe_iterable()

    def __iter__(self):
        """Iterate."""
        return self

    def __next__(self) -> PandaDataFrame:
        """Return the next PandaDataFrame.

        Raises:
            StopIteration: If there are no more pages.

        Returns:
            PandaDataFrame: The next page as a DataFrame.
        """
        data_frame: PandaDataFrame = next(self.__iterator)
        if data_frame.empty:
            raise StopIteration
        return data_frame


class DatabaseClient(DatabaseInterface):
    """BigQuery Database client."""

    def __init__(self) -> None:
        """Initialize the BigQuery Database client.

        Args:
            client (bigquery.Client): BigQuery client object.
        """
        logger.info("Initializing BigQuery Database client...")
        self.__client = bigquery.Client()
        # In BigQuery, the "database" is the project ID. Schemas are datasets.
        super().__init__(db_config)

    def __post_init__(self) -> None:
        """Post initialization."""
        # BigQuery doesn't have the same session concepts as Snowflake (role, warehouse)
        # We'll return the project ID.
        set_log_header(header=self.get_session_info())

    def __str__(self) -> str:
        """Return string representation of the database client."""
        return str(self.config)

    # ========== Metadata
    def get_session_info(self) -> dict[str, str]:
        """Extract session info for BigQuery."""
        # We'll return the project ID.
        return {
            LOG_HEADER_KEY_SERVER: "BigQuery",
            LOG_HEADER_KEY_DATABASE: self.__client.project,
        }

    def get_databases(self) -> list[str]:
        """Return list of database names.

        Returns:
            List[str]: List of database names.
        """
        return [project.project_id for project in self.__client.list_projects()]

    def get_default_database(self) -> str:
        """Return the default database name.

        Returns:
            str: Default database name.
        """
        return self.__client.project

    def get_schemas(self, database: str) -> list[str]:
        """Return list of schema names for a given database.

        Args:
            database (str): Database name

        Returns:
            List[str]: List of schema names.
        """
        return [dataset.dataset_id for dataset in self.__client.list_datasets(database)]

    def get_tables(self, database: str, schema: str) -> list[str]:
        """Return list of table names from the project and dataset.

        Args:
            database (str): GCP Project ID (maps from Snowflake database).
            schema (str): Dataset ID (maps from Snowflake schema).

        Returns:
            List[str]: List of table names.
        """
        if not database or not schema:
            return []
        # Internally, 'database' maps to project and 'schema' to dataset
        dataset_id = f"{database}.{schema}"
        tables = self.__client.list_tables(dataset_id)
        return [table.table_id for table in tables]

    def get_column_names(self, table: str) -> list[str]:
        """Return list of column names.

        Args:
             table (str): Full table ID in format `project.dataset.table`.

        Returns:
            List[str]: List of column names.
        """
        try:
            table = self.remove_table_quotation(table)
            bq_table = self.__client.get_table(table)
            return [field.name for field in bq_table.schema]
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"Failed to fetch columns for table: {table}",
            ) from err

    def get_column_data_types(self, table: str) -> dict[str, str]:
        """Return dictionary of column names with datatypes

        Args:
             table (str): Full table ID in format `project.dataset.table`.

        Returns:
            Dict[str,str]: dict of column names with dtypes
        """

        df = self.query_to_pandas(
            f"""
            SELECT * FROM {table} limit 1
        """
        )

        data = df.dtypes.to_dict()
        return {k: str(v) for k, v in data.items()}

    # ================== Table Operations
    def row_counts(self, table: str) -> int:
        """Return row counts of the table.

        Args:
            table (str): Table name

        Returns:
            int: Row counts
        """
        # Remove backticks
        table = table.replace("`", "")
        database, table_schema, table_name = self.parse_table(table)
        tquote = self.config.table_quotation
        sql = f"""
            SELECT total_rows AS records_count
            FROM
            {tquote}{database}.{table_schema}.INFORMATION_SCHEMA.PARTITIONS{tquote}
            WHERE table_name = "{table_name}"
        """.strip()
        data = self.query_to_dict(sql)
        if not data or len(data) == 0:
            return 0
        return data[0].get("records_count", 0)

    def row_counts_for_tables(
        self, database: str, schema: str, table_filters: Optional[List[str]] = None
    ) -> dict[str, int]:
        """Return row counts of all tables in the database and schema.

        Args:
            database (str): Database name
            schema (str): Schema name
            table_filters (Optional[List[str]], optional): List of table names to filter. Defaults to None.

        Returns:
            list[tuple[str, int]]: List of tuples with table names and row counts.
        """
        tquote = self.config.table_quotation
        sql = f"""
            SELECT table_name, total_rows AS row_counts
            FROM {tquote}{database}.{schema}.INFORMATION_SCHEMA.PARTITIONS{tquote}
        """.strip()
        if table_filters:
            sql += f" WHERE table_name IN ({', '.join(map(repr, table_filters))})"
        data = self.query_to_dict(sql)
        return {item["table_name"]: item["row_counts"] for item in data}

    def clone_table(
        self, source_table: str, destination_table: str, copy_data: bool = False
    ) -> None:
        """Create table with the specified schema, optionally copying data.

        Args:
            source_table (str): Source table ID.
            destination_table (str): Destination table ID.
            copy_data (bool, optional): Copy data from source to destination. Defaults to False.
        """
        if copy_data:
            # This creates a new table and copies the data.
            query = f"CREATE OR REPLACE TABLE {destination_table} CLONE {source_table}"
        else:
            # This creates an empty table with the same schema.
            query = f"CREATE OR REPLACE TABLE {destination_table} LIKE {source_table}"

        try:
            self.execute(query)
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"Failed to clone table. Query: {query}",
            ) from err

    def drop_table(self, table: str) -> None:
        """Drop this table.

        Args:
            table (str): Full table ID.
        """
        query = f"DROP TABLE IF EXISTS {table}"
        try:
            self.execute(query)
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"Failed to drop table. Query: {query}",
            ) from err

    def truncate_table(self, table: str) -> None:
        """Truncate this table.

        Args:
            table (str): Full table ID.
        """
        query = f"TRUNCATE TABLE {table}"
        try:
            self.execute(query)
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=f"Failed to truncate table. Query: {query}",
            ) from err

    def cast_to_string(self, column: str) -> str:
        """Return SQL to cast the column to string.

        Args:
            column (str): Column name

        Returns:
            str: SQL to cast the column to string
        """
        return f"CAST({column} AS STRING)"

    # ================== Execute SQL
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        """Execute SQL statement."""
        try:
            logger.debug("Executing SQL: %s, Params: %s", sql, params)
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(None, self._get_bq_type(p), p)
                    for p in params
                ]
            query_job = self.__client.query(sql, job_config=job_config)
            query_job.result()  # Wait for the job to complete
        except Exception as err:
            message = f"Failed to execute SQL: {sql}, Params: {params}"
            logger.error("%s. Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
                cause=err,
            ) from err

    def call_proc(self, proc_name: str, *args):
        """Call a BigQuery stored procedure."""
        try:
            logger.debug("Calling proc: %s, Args: %s", proc_name, args)
            # BigQuery CALL syntax is `CALL dataset.proc_name(args)`
            param_placeholders = ", ".join(["?"] * len(args))
            query = f"CALL `{proc_name}`({param_placeholders})"

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(None, self._get_bq_type(arg), arg)
                    for arg in args
                ]
            )

            query_job = self.__client.query(query, job_config=job_config)
            return query_job.result()
        except Exception as err:
            message = f"Failed to call procedure: {proc_name}, Params: {args}"
            logger.error("%s. [call_proc] Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
                cause=err,
            ) from err

    # ================== Write Data
    def append_data(self, dataframe: PandaDataFrame, table: str) -> None:
        """Append data to the destination table.

        Args:
            table (str): Table ID.
            dataframe (PandaDataFrame): Dataframe to append.
        """
        if dataframe.empty:
            logging.warning("Dataframe is empty, skipping append operation.")
            return

        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=False,  # For performance, schema should be defined or match
            )
            # logger.info("Appending %d records to table: %s. Dataframe columns:%s", len(dataframe), table, dataframe.columns.tolist())

            job = self.__client.load_table_from_dataframe(
                dataframe, table.strip("`"), job_config=job_config
            )
            job.result()  # Wait for the job to complete
        except Exception as err:
            columns = ", ".join([f"`{col}`" for col in dataframe.columns])
            message = (
                f"Failed to append data to table. Table: {table}."
                f"SQL from this dataframe:"
                f"SELECT {columns} FROM {table}"
            )
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
                cause=err,
            ) from err

    # ================== Query Data
    def table_to_pandas(
        self, table: str, columns: list[str] | None = None, limit: int = 0
    ) -> PandaDataFrame:
        """Query and return all records to Panda dataframe.

        Args:
            table (str): Table ID.
            columns (list[str] | None, optional): List of columns to select. Defaults to None (select all).
            limit (int, optional): Limit the number of records. Defaults to 0 (no limit).
        Returns:
            PandaDataFrame: Dataframe with records.
        """
        try:
            select_cols = "*"
            if columns:
                select_cols = f"{', '.join([f'`{c}`' for c in columns])}"

            query = f"SELECT {select_cols} FROM {table}"

            if limit > 0:
                query += f" LIMIT {limit}"

            return self.query_to_pandas(query)
        except Exception as err:
            message = f"Failed to fetch data to PandaDataFrame from table: {table}, Error: {err}"
            logger.error("%s. [table_to_pandas] Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
            ) from err

    def query_to_pandas(
        self, query_sql: str, params: Optional[Sequence[Any]] = None
    ) -> PandaDataFrame:
        """Query and return all records to a Pandas DataFrame."""
        try:
            logger.debug(
                "Executing query_to_pandas SQL: %s, Params: %s", query_sql, params
            )
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(None, self._get_bq_type(p), p)
                    for p in params
                ]

            query_job = self.__client.query(query_sql, job_config=job_config)
            return query_job.to_dataframe()
        except Exception as err:
            message = (
                f"Failed to query to PandaDataFrame: {query_sql}, Params: {params}"
            )
            logger.error("%s. [query_to_pandas] Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
                cause=err,
            ) from err

    def query_to_pandas_interator(
        self,
        query_sql: str,
        page_size: int = 1000,
        params: Optional[Sequence[Any]] = None,
    ) -> Iterable[PandaDataFrame]:
        """Return Panda Iterator to fetch records from this query."""
        logger.info(
            "Creating PandaBqQueryIterator with page size: %d. SQL:%s, Params:%s",
            page_size,
            query_sql,
            params,
        )
        try:
            logger.debug(
                "Executing query_to_pandas_interator SQL: %s, Params: %s",
                query_sql,
                params,
            )
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(None, self._get_bq_type(p), p)
                    for p in params
                ]
            query_job = self.__client.query(query_sql, job_config=job_config)
            return PandaBqQueryIterator(query_job, page_size)
        except Exception as err:
            message = (
                f"Failed to query to Panda Iterator: {query_sql}, Params: {params}"
            )
            logger.error("%s. [query_to_pandas_interator] Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
            ) from err

    def query_to_dict(
        self, query_sql: str, params: Optional[Sequence[Any]] = None
    ) -> list[dict]:
        """Query and return all records to List[dict]."""
        try:
            logger.debug(
                "Executing query_to_dict SQL: %s, Params: %s", query_sql, params
            )
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(None, self._get_bq_type(p), p)
                    for p in params
                ]
            query_job = self.__client.query(query_sql, job_config=job_config)
            return [dict(row) for row in query_job.result()]
        except Exception as err:
            message = f"Failed to query to List[dict]: {query_sql}, Params: {params}"
            logger.error("%s. [query_to_dict] Cause: %s", message, err)
            raise ClgxException(
                error=CommonErrorCodes.DB_GENERAL,
                message=message,
                cause=err,
            ) from err

    # ================== Helper Methods
    def _get_bq_type(self, value: Any) -> str:
        """Infers BigQuery type from Python type for query parameters."""
        if isinstance(value, int):
            return "INT64"
        if isinstance(value, float):
            return "FLOAT64"
        if isinstance(value, bool):
            return "BOOL"
        if isinstance(value, bytes):
            return "BYTES"
        # Add other type mappings as needed (e.g., for DATE, DATETIME, TIMESTAMP)
        return "STRING"
