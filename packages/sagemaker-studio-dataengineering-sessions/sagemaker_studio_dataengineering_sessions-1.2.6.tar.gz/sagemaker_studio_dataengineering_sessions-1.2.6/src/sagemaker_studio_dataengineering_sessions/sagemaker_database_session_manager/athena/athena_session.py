import os
import uuid

import botocore.config

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (
    CONNECTION_TYPE_ATHENA,
    DatabaseIntegrationConnectionAuthenticationTypes,
    DatabaseType,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.sql_workbench_gateway import (
    SqlWorkbenchGateway,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.athena.athena_config import (
    Config,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.athena.athena_debugging_helper import AthenaDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.athena.connection_transformer import (
    get_athena_connection,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.sagemaker_database_session_manager import (
    SageMakerDatabaseSessionManager,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.utils.common_utils import (
    get_athena_gamma_endpoint,
    get_sqlworkbench_endpoint,
)

USER_AGENT_SUFFIX = "sagemaker_unified_studio_connection_magic"
botocore_config = botocore.config.Config(user_agent_extra=USER_AGENT_SUFFIX)


class AthenaSession(SageMakerDatabaseSessionManager):
    def __init__(self, connection_name: str):
        self.connection_details = get_athena_connection(connection_name, self.get_logger())
        super().__init__(connection_name)
        self.config = Config()
        self.debugging_helper = AthenaDebuggingHelper(self)

    # legacy implementation
    def get_connection_parameter(self):
        # https://github.com/laughingman7743/PyAthena/blob/master/pyathena/connection.py#L49
        # https://code.amazon.com/packages/SMUnoSQLExecution/blobs/178ea494faca9f65a20d64e1358713c0f59eb381/--/src/amazon_sagemaker_sql_execution/athena/models.py#L41
        connection_properties: dict = {
            "work_group": self.connection_details.work_group,
            "connection_type": CONNECTION_TYPE_ATHENA,
            "profile_name": self.connection_details.connection_id,
            "region_name": self.connection_details.region,
        }
        if self.config.catalog_name:
            connection_properties["catalog_name"] = self.config.catalog_name
        if self.config.schema_name:
            connection_properties["schema_name"] = self.config.schema_name
        connection_properties["config"] = botocore_config
        if os.getenv("AWS_STAGE", None) == "GAMMA":
            connection_properties["endpoint_url"] = get_athena_gamma_endpoint(self.connection_details.region)
        return connection_properties

    def _build_connection_config(self) -> dict:
        """
        Build DatabaseConnectionConfiguration for SQL Workbench executeQuery API.
        """
        resource_identifier = self.connection_details.work_group

        if self.connection_details.enable_tip:
            auth_type = DatabaseIntegrationConnectionAuthenticationTypes.TRUSTED_IDENTITY_PROPAGATION
        else:
            auth_type = DatabaseIntegrationConnectionAuthenticationTypes.TEMPORARY_CREDENTIALS_WITH_IAM

        # Build base config
        return {
            "id": f"arn:aws:sqlworkbench:{self.connection_details.region}:{self.connection_details.account_id}:connection/{uuid.uuid4()!s}",
            "type": auth_type,
            "databaseType": DatabaseType.ATHENA,
            "connectableResourceIdentifier": resource_identifier,
            "connectableResourceType": "WORKGROUP",
        }

    def _create_sql_workbench_gateway(self):
        execution_context = [{"parentType": "DATABASE", "parentId": self.config.schema_name or "default"}]
        if self.config.catalog_name:
            execution_context.append({"parentType": "CATALOG", "parentId": self.config.catalog_name})
        self.sql_workbench_gateway = SqlWorkbenchGateway(
            sql_workbench_client=self.sql_workbench_client,
            connection_config=self._build_connection_config(),
            database_type=DatabaseType.ATHENA,
            execution_context=execution_context,
        )

    @staticmethod
    def _unload_query(query: str, s3_path: str):
        # Parse SQL statements and add a LIMIT clause if the statement type is SELECT
        return f"UNLOAD ({query}) TO '{s3_path}' WITH (format = 'PARQUET', compression = 'SNAPPY')"
