import logging
import time

import pandas as pd

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (
    DatabaseType,
    QueryExecutionStatus,
    QueryExecutionType,
    QueryResponseDeliveryType,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import (
    ExecutionException,
)

MAX_RETRIES = 5
RETRY_DELAY = 1  # 1 second
FINALIZED_STATUSES = [QueryExecutionStatus.FINISHED, QueryExecutionStatus.FAILED, QueryExecutionStatus.CANCELLED]
TAB_ID = "sagemaker_studio_jupyter_lab"


class SqlWorkbenchGateway:
    limit = 100

    def __init__(self, sql_workbench_client, connection_config, database_type: DatabaseType, execution_context):
        self.sql_workbench_client = sql_workbench_client
        self.logger = logging.getLogger(__name__)
        self.connection_config = connection_config
        self.database_type = database_type
        self.execution_context = execution_context

    def execute_query(self, sql_query) -> pd.DataFrame:
        try:
            result = self._execute_query_async(sql_query).get("queryResult")
            if result and result.get("errorMessage"):
                raise ExecutionException(f"Unable to process query. {result.get('errorMessage')}")
            return self._create_data_frame(result)
        except Exception as e:
            self.logger.error(f"Query execution failed {e.__class__.__name__}: {e}")
            raise

    def _execute_query_async(self, query: str) -> dict:
        """
        Execute query asynchronously using SQL Workbench executeQuery API.

        Args:
            query (str): SQL query to execute.

        Returns:
            Dict[str, Any]: Query execution result.

        Raises:
            ExecutionException: If query execution fails or cannot be tracked.
        """

        def execute():
            return self.sql_workbench_client.execute_query(
                connection=self.connection_config,
                databaseType=self.database_type,
                executionContext=self.execution_context,
                query=query,
                queryExecutionType=QueryExecutionType.NO_SESSION,
                queryResponseDeliveryType=QueryResponseDeliveryType.ASYNC,
                maxItems=100,
                tabId=TAB_ID,
                accountSettings={},
            )

        try:
            try:
                result = execute()
            except Exception as e:
                # Check if error has $metadata.httpStatusCode = 202
                metadata = getattr(e, "$metadata", {})
                if isinstance(metadata, dict) and metadata.get("httpStatusCode") == 202:
                    self.logger.info("Received 202 status code, retrying after delay...")
                    # Deep resume - wait 1 second and retry
                    time.sleep(RETRY_DELAY)
                    result = execute()
                else:
                    raise

            # Get query execution ID
            if result is not None and result.get("queryExecutions"):
                query_execution_status = result.get("queryExecutions")[0].get("queryExecutionStatus")
                query_execution_id = result.get("queryExecutions")[0].get("queryExecutionId")
                self.logger.info(f"Executing SQL query via SQLWorkbench: {query_execution_id}")
            else:
                raise ExecutionException("Unable to track query execution.")

            if query_execution_id and query_execution_status in FINALIZED_STATUSES:
                return result.get("queryExecutions")[0]

        except Exception as e:
            raise ExecutionException(f"Unable to process query. {e.__class__.__name__}: {e}")

        if not query_execution_id:
            raise ExecutionException("Query execution ID not found in response.")

        return self._poll_query_result(query_execution_id)

    def _poll_query_result(self, query_execution_id: str) -> dict:
        """
        Poll for query execution results and return them when ready.

        Args:
            query_execution_id (str): The ID of the query execution to poll.

        Returns:
            Dict[str, Any]: The query result.

        Raises:
            ExecutionException: If the query exceeds the maximum execution time or fails.
        """
        try:
            ack_ids = []
            is_finalized = False
            retry_count = 0

            while not is_finalized and retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                poll_result = self.sql_workbench_client.poll_query_execution_events(
                    queryExecutionIds=[query_execution_id],
                    databaseType=self.database_type,
                    ackIds=ack_ids,
                    accountSettings={},
                )

                for event in poll_result.get("events"):
                    if event.get("queryExecutionId") == query_execution_id:
                        is_finalized = is_finalized or event.get("queryExecutionStatus") in FINALIZED_STATUSES
                        break
                    if event.get("ackId"):
                        ack_ids.append(event.get("ackId"))
                retry_count += 1

        except Exception as e:
            raise ExecutionException(f"Error while polling query {query_execution_id}. {e.__class__.__name__}: {e}")

        if not is_finalized:
            raise ExecutionException(f"Query {query_execution_id} exceeded the maximum execution time.")

        # Get results
        try:
            result = self.sql_workbench_client.get_query_result(
                queryExecutionId=query_execution_id,
                databaseType=self.database_type,
                accountSettings={},
            )
        except Exception as e:
            raise ExecutionException(
                f"Failed to retrieve result for query {query_execution_id}. {e.__class__.__name__}: {e}"
            )

        return result

    def _create_data_frame(self, result: dict) -> pd.DataFrame:
        try:
            # Handle empty results
            if not result:
                return None

            data = {"headers": result.get("headers"), "rows": result.get("rows")}  # Table columns  # Table rows

            # Handle empty rows
            if not data.get("rows"):
                return None

            # Handle single row results (e.g., COUNT queries)
            if len(data.get("rows")) == 1:
                return data.get("rows")[0]["row"]

            column_names = [header["displayName"] for header in data["headers"]]
            column_types = [header["type"] for header in data["headers"]]

            # Create dtype dictionary
            dtypes = {
                name: self._get_pandas_dtype(dtype) for name, dtype in zip(column_names, column_types, strict=False)
            }

            # Extract row data
            rows_data = [row["row"] for row in data["rows"]]

            # Create initial DataFrame
            df = pd.DataFrame(rows_data, columns=column_names)

            # Apply conversions with error handling for each column
            for col, dtype in dtypes.items():
                try:
                    if dtype == "boolean":
                        df[col] = self._convert_to_boolean(df[col])
                    elif dtype.startswith("datetime"):
                        df[col] = self._convert_to_datetime(df[col])
                    else:
                        df[col] = df[col].astype(dtype)
                except Exception as e:
                    self.logger.warning(f"Could not convert column {col} to {dtype}. {e.__class__.__name__}: {e}")
                    # Keep the original data if conversion fails

            return df

        except Exception as e:
            raise ExecutionException(f"Unable to process the query results. {e.__class__.__name__}: {e}")

    @staticmethod
    def _convert_to_boolean(series: pd.Series) -> pd.Series:
        """Convert string boolean values to actual boolean"""
        if series.dtype == "object":
            return series.map(
                {
                    "true": True,
                    "false": False,
                    "TRUE": True,
                    "FALSE": False,
                    "True": True,
                    "False": False,
                    "1": True,
                    "0": False,
                }
            )
        return series

    @staticmethod
    def _convert_to_datetime(series: pd.Series) -> pd.Series:
        # Create result Series with same index as input
        result = pd.Series(index=series.index, dtype="datetime64[ns]")

        # Handle null values first
        is_null = series.isna()
        result[is_null] = pd.NaT

        # Exit early if all values are null
        if is_null.all():
            return result

        # Work with non-null values only
        non_null_series = series[~is_null]

        # First attempt with pandas inference (fastest for common formats)
        parsed = pd.to_datetime(non_null_series, infer_datetime_format=True, errors="coerce")

        # Fill in successfully parsed values
        result[~is_null] = parsed

        # Check if any values failed to parse
        failed_parse = result.isna() & ~is_null
        if not failed_parse.any():
            return result

        # Replace failed parses with original string values
        result[failed_parse] = series[failed_parse]

        return result

    @staticmethod
    def _get_pandas_dtype(sql_type) -> str:
        """Map SQL data types to pandas dtypes"""
        type_mapping = {
            # Numeric types
            "INTEGER": "Int64",  # nullable integer
            "BIGINT": "Int64",
            "SMALLINT": "Int64",
            "BIG_DECIMAL": "Float64",  # nullable float
            "DECIMAL": "Float64",
            "DOUBLE": "Float64",
            "FLOAT": "Float64",
            # String types
            "STRING": "string",
            "VARCHAR": "string",
            "CHAR": "string",
            "TEXT": "string",
            # Boolean type
            "BOOLEAN": "boolean",
            # Date/Time types
            "DATE": "datetime64[ns]",
            "TIMESTAMP": "datetime64[ns]",
            "TIME": "datetime64[ns]",
            "DATETIME": "datetime64[ns]",
            "DATETIME_TZ": "datetime64[ns]",
            # Default
            "UNKNOWN": "object",
        }
        return type_mapping.get(sql_type.upper(), "object")
