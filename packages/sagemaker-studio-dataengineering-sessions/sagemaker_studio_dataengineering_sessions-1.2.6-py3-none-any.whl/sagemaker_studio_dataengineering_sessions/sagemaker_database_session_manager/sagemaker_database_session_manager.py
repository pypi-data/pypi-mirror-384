import json
import os

import pandas as pd
import sqlparse
from amazon_sagemaker_sql_execution.exceptions import CredentialsExpiredError
from amazon_sagemaker_sql_execution.models.sql_execution import SQLExecutionRequest
from IPython import get_ipython
from sqlparse import keywords
from sqlparse.lexer import Lexer

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_session_manager import (
    BaseSessionManager,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import (
    create_sql_workbench_client,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (
    CONNECTION_TYPE_REDSHIFT,
    Language,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.debugging_utils import get_cell_content, get_cell_id
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import (
    ExecutionException,
    LanguageNotSupportedException,
    SessionExpiredError,
    StartSessionException,
    StopSessionException,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import (
    SageMakerConnectionDisplay,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.ipython_display_compute import (
    IpythonDisplayCompute,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.db_connection_pool import (
    DatabaseConnectionPool,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.display.database_display_renderer import (
    DatabaseDisplayRenderer,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.utils.common_utils import (
    get_sqlworkbench_endpoint,
)


class SageMakerDatabaseSessionManager(BaseSessionManager):
    def __init__(self, connection_name: str):
        super().__init__()
        self.connection_name = connection_name
        self.active_connection = None
        self.connection_pool = DatabaseConnectionPool()

        # Creating a sql workbench client
        self.is_gamma = os.getenv("AWS_STAGE", None) == "GAMMA"
        region = self.connection_details.region
        sql_workbench_endpoint = get_sqlworkbench_endpoint(region=region, is_gamma=self.is_gamma)
        self.sql_workbench_client = create_sql_workbench_client(
            profile=self.profile,
            region=region,
            endpoint_url=sql_workbench_endpoint,
        )
        self.sql_workbench_gateway = None
        self.debugging_helper = None

    def get_connection_parameter(self) -> dict:
        raise NotImplementedError("get_connection_parameter has not been implemented yet")

    def create_session(self):
        if not self.config.use_sql_workbench:
            # If 'use_sql_workbench' is set to False in the configuration, use the legacy method
            self._create_session()
        else:
            self._create_sql_workbench_gateway()

    def _create_session(self):
        # get the connection details using SageMaker CLI and translates
        # the connection details into connection props that amazon_sagemaker_sql_execution expects, calls
        # amazon_sagemaker_sql_execution's SQL Factory to create the connection if needed.
        database_connection_properties = self.get_connection_parameter()
        try:
            self.active_connection = self.connection_pool.get_or_create_connection(
                metastore_type=None,
                metastore_id=None,
                connection_parameters=database_connection_properties,
                connection_name=self.connection_name,
            )
        except Exception as e:
            self.get_logger().error(
                f"Could not create session for connection {self.connection_name} because of {e.__class__.__name__}: {e}"
            )
            raise StartSessionException(
                f"Could not create session for connection {self.connection_name} because of {e.__class__.__name__}: {e}"
            ) from e
        finally:
            del database_connection_properties

    def run_statement(self, cell="", language=Language.sql, storage=None, **kwargs):
        if not language.supports_connection_type(CONNECTION_TYPE_REDSHIFT):
            raise LanguageNotSupportedException(f"Language {language.name} not supported for Redshift")
        
        interactive_debugging = kwargs.get('interactive_debugging', True)

        # parse the SQL query
        # execute the SQL query using this connection
        row_limit = self.sql_result_row_limit
        sql_query = self._parse_sql_query(cell)

        new_statement = sql_query[0].value
        if sql_query[0].get_type() == "SELECT" and row_limit is not None:
            new_statement = f"SELECT * FROM ({sql_query[0].value}) as limited_subquery LIMIT {row_limit}"
            
        if self.debugging_helper and interactive_debugging:
            self.debugging_helper.prepare_statement(new_statement)

        result = self._run_query(new_statement, interactive_debugging, row_limit)
        get_ipython().user_ns['_'] = result
        return result

    def _run_query(self, sql_query, interactive_debugging=False, row_limit: int = None):
        try: 
            if self.config.use_sql_workbench:
                return self.sql_workbench_gateway.execute_query(sql_query)
            else:
                # If 'use_sql_workbench' is set to False in the configuration, use the legacy method
                return self._run_query_legacy(sql_query, row_limit)
        except Exception as e:
            # Get cell_id and cell_content before checking conditions
            cell_id = get_cell_id()
            cell_content = get_cell_content()
            
            # Write debugging info if conditions are met
            if self.debugging_helper and interactive_debugging:
                self.debugging_helper.write_debugging_info(
                    cell_id=cell_id if cell_id else "unknown_cell_id", 
                    cell_content=cell_content,
                    error_message=str(e)
                )
            raise e
                

    def _run_query_legacy(self, sql_query, row_limit: int = None):
        execution_request = SQLExecutionRequest(sql_query, {})
        try:
            response = self.active_connection.execute(execution_request)
        except CredentialsExpiredError as e:
            self.get_logger().error(f"Could not run statement because of {e}")
            self.connection_pool.close_cached_connection(self.active_connection)
            self.active_connection = None
            raise SessionExpiredError(
                f"The session for SageMaker connection {self.connection_name} has expired and was closed, please rerun the query"
            )
        column_names = [columnMetadataEntry.name for columnMetadataEntry in response.column_metadata]
        # We can add this as an output paramater similar to amazon_sagemaker_sql_execution
        if not response.data:  # Empty Response
            return None
        if len(response.data) == 1:  # Single Row (i.e., asking for count)
            return response.data[0]
        return pd.DataFrame(response.data, columns=column_names)  # else return dataframe

    def _parse_sql_query(self, query):
        # Strip comments from query
        # Expect a single query in statement. connection magic should already split the cell to queries.
        formatted_query = sqlparse.format(query, strip_comments=True)

        # Handle leading parenthesis during parsing as sqlparse does not do this by default
        # See https://sqlparse.readthedocs.io/en/latest/extending.html
        lex = Lexer.get_default_instance()
        leading_parenthesis_regex = ("^(\\s*\\(\\s*)+", sqlparse.tokens.Comment)
        lex.set_SQL_REGEX([leading_parenthesis_regex] + keywords.SQL_REGEX)

        # Parse SQL statements and add a LIMIT clause if the statement type is SELECT
        return sqlparse.parse(formatted_query)

    def stop_session(self):
        if not self.config.use_sql_workbench:
            # If 'use_sql_workbench' is set to False in the configuration, use the legacy method
            self._stop_session()
        else:
            self.sql_workbench_gateway = None

    def _stop_session(self):
        # if active connection exists, close the active connection.
        try:
            if self.active_connection:
                self.connection_pool.close_connection(self.connection_name)
        except Exception as e:
            self.get_logger().error(
                f"Could not stop session for connection {self.connection_name} "
                f"because of {e.__class__.__name__}: {e}"
            )
            raise StopSessionException(
                f"Could not stop session for connection {self.connection_name} "
                f"because of {e.__class__.__name__}: {e}"
            ) from e

    def is_session_connectable(self) -> bool:
        if not self.config.use_sql_workbench:
            # If 'use_sql_workbench' is set to False in the configuration, use the legacy method
            return self._is_session_connectable()
        else:
            return self.sql_workbench_gateway is not None

    def _is_session_connectable(self) -> bool:
        # check if active connection is not None
        if self.active_connection:
            return True
        return False

    def _create_display_renderer(self, statement: str, *args, **kwargs):
        try:
            display_compute_id = kwargs.get("display_compute_id")
            get_ipython().user_ns[display_compute_id] = IpythonDisplayCompute(*args, **kwargs)
            query = self._parse_sql_query(statement)[0].value
            return DatabaseDisplayRenderer(
                session_manager=self,
                query=query,
                limit=self.sql_result_row_limit if not self.config.use_sql_workbench else self.sql_workbench_gateway.limit,
                data_uuid=kwargs.get("display_uuid"),
                display_magic_compute=display_compute_id,
                storage=kwargs.get("storage"),
                query_result_s3_suffix=kwargs.get("query_result_s3_suffix"),
                enable_profiling=kwargs.get("enable_profiling"),
            )
        except Exception as e:
            self.get_logger().error(f"Could not create display compute: {e}")
            return None

    def unload(self, query: str, s3_path: str):
        unload_query = self._unload_query(query, s3_path)
        self._run_query(unload_query)

    def count(self, query: str):
        try:
            count_statement = f"SELECT COUNT(*) FROM ({query})"
            return self._run_query(count_statement)[0]
        except Exception as e:
            self.get_logger().warning(f"Failed to count dataframe size: {e.__class__.__name__}: {e}")
            return None

    def _configure_core(self, cell: str):
        try:
            configurations = json.loads(cell)
        except ValueError:
            SageMakerConnectionDisplay.send_error(f"Could not parse JSON object from input '{format(cell)}'")
            self.get_logger().error(f"Could not parse JSON object from input '{format(cell)}'")
            return

        if not configurations:
            SageMakerConnectionDisplay.send_error("No configuration values were provided.")
            self.get_logger().error("No configuration values were provided.")
            return

        if self.config:
            for arg, val in configurations.items():
                if arg == "use_sql_workbench":
                    setattr(self.config, arg, False if val.casefold() == "false" else True)
                elif hasattr(self.config, arg):
                    setattr(self.config, arg, val)

            # Filter out None value from config cache
            not_none_config = {key: value for key, value in vars(self.config).items() if value is not None}
            SageMakerConnectionDisplay.display(f"The following configurations have been updated: {not_none_config}")

    def _unload_query(self, query, s3_path: str):
        raise NotImplementedError("Please implement the function to generate an unload query.")

    def _create_sql_workbench_gateway(self):
        raise NotImplementedError("Please implement _create_sql_workbench_gateway function.")
