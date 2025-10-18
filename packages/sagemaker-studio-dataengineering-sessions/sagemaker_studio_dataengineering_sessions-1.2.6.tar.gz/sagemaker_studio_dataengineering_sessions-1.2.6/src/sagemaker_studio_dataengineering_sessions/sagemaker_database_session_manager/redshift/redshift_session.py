import uuid
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (
    CONNECTION_TYPE_REDSHIFT,
    EXECUTION_ROLE_ARN,
    DatabaseIntegrationConnectionAuthenticationTypes,
    DatabaseType,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.sql_workbench_gateway import (
    SqlWorkbenchGateway,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.connection_transformer import (
    AUTH_TYPE_SECRET_MANAGER,
    get_redshift_connection,
    get_redshift_connection_credentials,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.redshift_config import (
    Config,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.redshift_debugging_helper import RedshiftDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.sagemaker_database_session_manager import (
    SageMakerDatabaseSessionManager,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.utils.common_utils import (
    get_redshift_gamma_endpoint,
    get_redshift_serverless_gamma_endpoint,
)

REDSHIFT_HOST_KEYWORD = "redshift.amazonaws"
REDSHIFT_DEV_HOST_KEYWORD = "redshift-dev.amazonaws"
MAX_RETRIES = 5
RETRY_DELAY = 1  # 1 second


class RedshiftSession(SageMakerDatabaseSessionManager):
    def __init__(self, connection_name: str):
        # Get connection details first so we have them available
        self.connection_details = get_redshift_connection(connection_name, self.get_logger())
        super().__init__(connection_name)
        self.config = Config()
        self.debugging_helper = RedshiftDebuggingHelper(self)

    def get_connection_parameter(self) -> dict:
        # https://code.amazon.com/packages/SMUnoSQLExecution/blobs/178ea494faca9f65a20d64e1358713c0f59eb381/--/src/amazon_sagemaker_sql_execution/redshift/models.py#L37
        connection_properties: dict = {
            "host": self.connection_details.host,
            "database": self.connection_details.database,
            "port": self.connection_details.port,
            "connection_type": CONNECTION_TYPE_REDSHIFT,
            "region": self.connection_details.region,
        }
        gamma_endpoint = get_redshift_gamma_endpoint(self.connection_details.region)
        serverless_gamma_endpoint = get_redshift_serverless_gamma_endpoint(self.connection_details.region)
        if self.connection_details.auth_type == AUTH_TYPE_SECRET_MANAGER:
            username, password = get_redshift_connection_credentials(self.connection_details.connection_id)
            connection_properties["user"] = username
            connection_properties["password"] = password
            # for Redshift Cluster, cluster_identifier is required, which is not required for Redshift-Serverless
            # sample host:
            # RS Cluster: default-rs-cluster.cmlomtaja7gk.us-west-2.redshift.amazonaws.com
            # RS Workgroup: default-workgroup.123456789012.us-west-2.redshift-serverless.amazonaws.com
            if (
                REDSHIFT_HOST_KEYWORD in self.connection_details.host
                or REDSHIFT_DEV_HOST_KEYWORD in self.connection_details.host
            ):
                connection_properties["cluster_identifier"] = self.connection_details.host.split(".")[0]
                if self.is_gamma:
                    connection_properties["endpoint_url"] = gamma_endpoint
            else:
                connection_properties["serverless_work_group"] = self.connection_details.host.split(".")[0]
                if self.is_gamma:
                    connection_properties["endpoint_url"] = serverless_gamma_endpoint
        # At the time of this commit, the else logic would be FEDERATED
        # We set the default case to IAM mode
        # in case redshiftAuthType is missing from connection to be backward compatible
        else:
            # IAM authentication is set to be True.
            # We use an AWS profile which is created in SageMakerConnectionMagic
            # https://code.amazon.com/packages/SageMakerConnectionMagic/blobs/93998b3d11d8f65d7c6e52f0d04638d6862ad454/--/sagemaker_connection_magic/sagemaker_connection_magic.py#L187
            # The profile will fetch creds for default IAM connection
            connection_properties["iam"] = True
            connection_properties["profile"] = self.connection_details.connection_id
            # for Redshift Cluster, cluster_identifier is required, which is not required for Redshift-Serverless
            # sample host:
            # RS Cluster: default-rs-cluster.cmlomtaja7gk.us-west-2.redshift.amazonaws.com
            # RS Workgroup: default-workgroup.851725315372.us-west-2.redshift-serverless.amazonaws.com
            if (
                REDSHIFT_HOST_KEYWORD in self.connection_details.host
                or REDSHIFT_DEV_HOST_KEYWORD in self.connection_details.host
            ):
                connection_properties["cluster_identifier"] = self.connection_details.host.split(".")[0]
                # A special flag to instruct redshift_connector to use Redshift:GetClusterCredentialsWithIam API
                # Ref: https://github.com/aws/amazon-redshift-python-driver/blob/26fc02dd860a31daf31b92b4ccf1ef66a09f3cdf/redshift_connector/iam_helper.py#L84-L89
                connection_properties["group_federation"] = True
                if self.is_gamma:
                    connection_properties["endpoint_url"] = gamma_endpoint
            else:
                connection_properties["serverless_work_group"] = self.connection_details.host.split(".")[0]
                if self.is_gamma:
                    connection_properties["endpoint_url"] = serverless_gamma_endpoint
        return connection_properties

    def _build_connection_config(self) -> dict:
        """
        Build DatabaseConnectionConfiguration for SQL Workbench executeQuery API.
        """
        # Get resource identifier from host (first part before first dot)
        # redshift-serverless-workgroup-cq6mjtqcyfzuhc.949829876266.us-west-2.redshift-serverless.amazonaws.com -> redshift-serverless-workgroup-cq6mjtqcyfzuhc
        resource_identifier = self.connection_details.host.split(".")[0]

        # Determine if serverless or cluster based on host
        is_serverless = "redshift-serverless" in self.connection_details.host

        # Determine auth type
        if self.connection_details.enable_tip:
            auth_type = DatabaseIntegrationConnectionAuthenticationTypes.TRUSTED_IDENTITY_PROPAGATION
        elif self.connection_details.auth_type == AUTH_TYPE_SECRET_MANAGER:
            auth_type = DatabaseIntegrationConnectionAuthenticationTypes.SECRET
        else:
            # For serverless use FEDERATED, for cluster use TEMPORARY_CREDENTIALS_WITH_IAM
            auth_type = (
                DatabaseIntegrationConnectionAuthenticationTypes.FEDERATED
                if is_serverless
                else DatabaseIntegrationConnectionAuthenticationTypes.TEMPORARY_CREDENTIALS_WITH_IAM
            )

        # Build base config
        config = {
            "id": f"arn:aws:sqlworkbench:{self.connection_details.region}:{self.connection_details.account_id}:connection/{uuid.uuid4()!s}",
            "type": auth_type,
            "databaseType": DatabaseType.REDSHIFT,
            "connectableResourceIdentifier": resource_identifier,
            "connectableResourceType": "WORKGROUP" if is_serverless else "CLUSTER",
            "database": self.connection_details.database,
        }

        # Add auth if using secrets manager
        if self.connection_details.auth_type == AUTH_TYPE_SECRET_MANAGER:
            config["auth"] = {"secretArn": self.connection_details.secret_arn}

        return config

    def _create_sql_workbench_gateway(self):
        connection_config = self._build_connection_config()
        execution_context = [
            {"parentType": "DATABASE", "parentId": self.config.catalog_name or connection_config.get("database")}
        ]
        if self.config.schema_name:
            execution_context.append({"parentType": "SCHEMA", "parentId": self.config.schema_name})
        self.sql_workbench_gateway = SqlWorkbenchGateway(
            sql_workbench_client=self.sql_workbench_client,
            connection_config=connection_config,
            database_type=DatabaseType.REDSHIFT,
            execution_context=execution_context,
        )

    @staticmethod
    def _unload_query(query: str, s3_path: str):
        # Parse SQL statements and add a LIMIT clause if the statement type is SELECT
        return f"UNLOAD ('{query}') TO '{s3_path}/' IAM_ROLE '{EXECUTION_ROLE_ARN}' PARQUET"
