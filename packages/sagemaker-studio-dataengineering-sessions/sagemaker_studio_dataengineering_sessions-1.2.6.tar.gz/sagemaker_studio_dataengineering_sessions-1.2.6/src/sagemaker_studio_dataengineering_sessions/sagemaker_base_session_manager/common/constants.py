import json
import logging
import os
from enum import Enum, unique

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.metadata_utils import retrieve_sagemaker_metadata_from_file, \
    retrieve_sagemaker_storage_metadata_from_file

# Metadata key definition is in LooseLeafWorkflowsLambda
# https://code.amazon.com/packages/LooseLeafWorkflowsLambda/blobs/mainline/--/src/com/amazon/looseleafworkflowslambda/job/MaxDomeMetadataHelper.java

logger = logging.getLogger(__name__)

def _get_sagemaker_domain_id(metadata) -> str:
    if metadata and 'DomainId' in metadata :
        return metadata['DomainId']
    return ""

def _get_sagemaker_space_name(metadata) -> str:
    if metadata and 'SpaceName' in metadata :
        return metadata['SpaceName']
    return ""


def _get_datazone_user_id(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneUserId' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneUserId']
    return os.getenv(DATAZONE_USER_ID_ENV, None)

def _get_datazone_domain_id(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneDomainId' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneDomainId']
    domain_id = os.getenv(DATAZONE_DOMAIN_ID_ENV, None)
    return domain_id


def _get_datazone_project_id(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneProjectId' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneProjectId']
    project_id = os.getenv(DATAZONE_PROJECT_ID_ENV, None)
    return project_id

def _get_datazone_environment_id(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneEnvironmentId' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneEnvironmentId']
    return os.getenv(DATAZONE_ENVIRONMENT_ID_ENV, None)

def _get_datazone_stage(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneStage' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneStage']
    return os.getenv(DATAZONE_STAGE_ENV, None)

def _get_datazone_endpoint_url(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneEndpoint' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneEndpoint']
    datazone_endpoint = os.getenv(DATAZONE_ENDPOINT_ENV, None)
    return datazone_endpoint

def _get_project_s3_path(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'ProjectS3Path' in metadata['AdditionalMetadata']:
        s3path = metadata['AdditionalMetadata']['ProjectS3Path']
    else:
        s3path = os.getenv(PROJECT_S3_PATH_ENV, None)
    if s3path and s3path.endswith("/"):
        s3path = s3path[:-1]
    return s3path


def _get_datazone_region(metadata) -> str | None:
    if metadata and 'AdditionalMetadata' in metadata and 'DataZoneDomainRegion' in metadata['AdditionalMetadata']:
        return metadata['AdditionalMetadata']['DataZoneDomainRegion']
    datazone_region = os.getenv(DATAZONE_DOMAIN_REGION_ENV, None)
    return datazone_region

def _get_execution_role_arn(metadata) -> str | None:
    if metadata and metadata['ExecutionRoleArn']:
        return metadata['ExecutionRoleArn']
    return os.getenv(EXECUTION_ROLE_ARN_ENV, None)

def _get_lib_path(metadata, storage_metadata) -> str:
    return '/'.join([_get_workspace_path(metadata, storage_metadata), '.libs.json'])

def _get_workspace_path(metadata, storage_metadata) -> str:
    default_path = os.path.expanduser("~/src")
    if metadata and 'AdditionalMetadata' in metadata and 'ProjectSharedDirectory' in metadata['AdditionalMetadata']:
        default_path = metadata['AdditionalMetadata']['ProjectSharedDirectory']
    elif storage_metadata and storage_metadata['smusProjectDirectory']:
        default_path = storage_metadata['smusProjectDirectory']
    path = os.getenv(SM_EXECUTION_INPUT_PATH_ENV, default=default_path)
    return path

def _get_connection_name_override() -> dict[str, str]:
    overrides_json_str = os.getenv(CONNECTION_NAME_OVERRIDES_ENV, "")
    if not overrides_json_str:
        return {}
    try:
        overrides = json.loads(overrides_json_str)
        for key, value in overrides.items():
            if not isinstance(key, str) or not isinstance(value, str):
                logger.warning(f"Ignoring connection_name_override, "
                               f"bacause connection_name_override has non-str key/value: {key} : {value}")
                return {}
        return overrides
    except json.JSONDecodeError:
        logger.warning(f"Ignoring connection_name_override, "
                       f"bacause connection_name_override has invalid json format: {overrides_json_str}")
        return {}

def _get_input_notebook_path() -> str | None:
    return os.getenv(INPUT_NOTEBOOK_PATH_ENV, default=None)

def _get_is_triggered_from_remote_workflow(metadata) -> bool:
    if metadata:
        return False
    else:
        return True

AWS_REGION_ENV = "AWS_REGION"

CONNECTION_TYPE_ATHENA = "ATHENA"
CONNECTION_TYPE_REDSHIFT = "REDSHIFT"
CONNECTION_TYPE_SPARK_EMR_EC2 = "SPARK_EMR_EC2"
CONNECTION_TYPE_SPARK_GLUE = "SPARK_GLUE"
CONNECTION_TYPE_SPARK_EMR_SERVERLESS = "SPARK_EMR_SERVERLESS"
CONNECTION_TYPE_IAM = "IAM"
CONNECTION_TYPE_GENERAL_SPARK = "SPARK"

CONNECTION_MAGIC_PYSPARK = "%%pyspark"
CONNECTION_MAGIC_SCALASPARK = "%%scalaspark"
CONNECTION_MAGIC_SQL = "%%sql"
CONNECTION_MAGIC_CONFIGURE = "%%configure"

CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT = "-n"
CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG = "--name"

CONFIGURATION_NAME_GLUE_DEFAULT_ARGUMENTS = "GlueDefaultArgument"
CONFIGURATION_NAME_SPARK_CONFIGURATIONS = "SparkConfiguration"
CONFIGURATION_NAME_SPARK_DEFAULTS = "spark-defaults"

CONNECTION_TYPE_SPARK = [CONNECTION_TYPE_SPARK_EMR_SERVERLESS,
                         CONNECTION_TYPE_SPARK_EMR_EC2,
                         CONNECTION_TYPE_SPARK_GLUE]

CONNECTION_TYPE_NOT_SPARK = [CONNECTION_TYPE_ATHENA,
                             CONNECTION_TYPE_REDSHIFT,
                             CONNECTION_TYPE_IAM]

#
# https://code.amazon.com/packages/MaxDomePythonSDK/blobs/c99d3f86a92ba86f6f5c84e2509a2870d955e44c/--/src/maxdome/execution/remote_execution_client.py#L396-L399
CONNECTION_NAME_OVERRIDES_ENV = "ConnectionNameOverrides"
DATAZONE_USER_ID_ENV = "DataZoneUserId"
DATAZONE_DOMAIN_ID_ENV = "DataZoneDomainId"
DATAZONE_DOMAIN_REGION_ENV = "DataZoneDomainRegion"
DATAZONE_PROJECT_ID_ENV = "DataZoneProjectId"
DATAZONE_ENVIRONMENT_ID_ENV = "DataZoneEnvironmentId"
DATAZONE_STAGE_ENV = "DataZoneStage"
DATAZONE_ENDPOINT_ENV = "DataZoneEndpoint"
INPUT_NOTEBOOK_PATH_ENV = "InputNotebookPath"
PROJECT_S3_PATH_ENV = "ProjectS3Path"
SMUS_PROJECT_DIR_ENV = "SMUS_PROJECT_DIR"
SM_EXECUTION_INPUT_PATH_ENV = "SM_EXECUTION_INPUT_PATH"

EXECUTION_ROLE_ARN_ENV = "ExecutionRoleArn"

SAGEMAKER_DEFAULT_CONNECTION_NAME = "project.iam"
SAGEMAKER_DEFAULT_CONNECTION_NAME_EXPRESS = 'default.iam'
SAGEMAKER_DEFAULT_CONNECTION_DISPLAYNAME = "project.python"
SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_DEPRECATED = "project.spark"
SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_EXPRESS = "default.spark"
SAGEMAKER_DEFAULT_GLUE_COMPATIBILITY_CONNECTION_NAME = "project.spark.compatibility"
SAGEMAKER_DEFAULT_GLUE_FINE_GRAINED_CONNECTION_NAME = "project.spark.fineGrained"
SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME = "project.athena"
SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME_EXPRESS = "default.sql"
SAGEMAKER_DEFAULT_REDSHIFT_CONNECTION_NAME = "project.redshift"
SAGEMAKER_DEFAULT_REDSHIFT_CONNECTION_NAME_EXPRESS = "default.catalog"
DEFAULT_IPYTHON_NAME = "_ipython_default"

GET_IPYTHON_SHELL = "get_ipython()"
METADATA_CONTENT = retrieve_sagemaker_metadata_from_file()
STORAGE_METADATA_CONTENT = retrieve_sagemaker_storage_metadata_from_file()

USER_ID = _get_datazone_user_id(METADATA_CONTENT)
DOMAIN_ID = _get_datazone_domain_id(METADATA_CONTENT)
PROJECT_ID = _get_datazone_project_id(METADATA_CONTENT)
DATAZONE_ENDPOINT_URL = _get_datazone_endpoint_url(METADATA_CONTENT)
DATAZONE_DOMAIN_REGION = _get_datazone_region(METADATA_CONTENT)
DATAZONE_STAGE = _get_datazone_stage(METADATA_CONTENT)
DATAZONE_ENVIRONMENT_ID = _get_datazone_environment_id(METADATA_CONTENT)
PROJECT_S3_PATH = _get_project_s3_path(METADATA_CONTENT)
EXECUTION_ROLE_ARN = _get_execution_role_arn(METADATA_CONTENT)
LIB_PATH = _get_lib_path(METADATA_CONTENT, STORAGE_METADATA_CONTENT)
CONNECTION_NAME_OVERRIDES = _get_connection_name_override()
IS_REMOTE_WORKFLOW = _get_is_triggered_from_remote_workflow(METADATA_CONTENT)
INPUT_NOTEBOOK_PATH = _get_input_notebook_path()
SAGEMAKER_DOMAIN_ID = _get_sagemaker_domain_id(METADATA_CONTENT)
SAGEMAKER_SPACE_NAME = _get_sagemaker_space_name(METADATA_CONTENT)

# Default directory template for debugging information
DEFAULT_DEBUGGING_DIR_TEMPLATE = "/tmp/temp_sagemaker_unified_studio_debugging_info/{cell_id}"
DEFAULT_DEBUGGING_DIR_PARENT = "/tmp/temp_sagemaker_unified_studio_debugging_info"
SYMLINK_DEBUGGING_DIR_TEMPLATE = os.path.join(_get_workspace_path(METADATA_CONTENT, STORAGE_METADATA_CONTENT), ".temp_sagemaker_unified_studio_debugging_info/{cell_id}")
SYMLINK_DEBUGGING_DIR_PARENT = os.path.join(_get_workspace_path(METADATA_CONTENT, STORAGE_METADATA_CONTENT), ".temp_sagemaker_unified_studio_debugging_info")
DEBUGGING_INFO_CENTRAL_LOG_DIR = "/var/log/studio/interactive_debugging_info"
DEBUGGING_INFO_CENTRAL_LOG_FILE = "interactive_debugging_info.log"
METRICS_NAMESPACE = "SageMaker/InteractiveDebugging"

#  SQL Workbench API Constants
class DatabaseIntegrationConnectionAuthenticationTypes(str, Enum):
    """Authentication types for database connections in SQL Workbench API"""
    FEDERATED = 4
    TEMPORARY_CREDENTIALS_WITH_IAM = 5
    SECRET = 6
    TRUSTED_IDENTITY_PROPAGATION = 8


class DatabaseType(str, Enum):
    """Database types supported by SQL Workbench API"""
    REDSHIFT = "REDSHIFT"
    ATHENA = "ATHENA"


class QueryExecutionStatus(str, Enum):
    """Status values for query execution in SQL Workbench API"""
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QueryExecutionType(str, Enum):
    """Query execution types in SQL Workbench API"""
    NO_SESSION = "NO_SESSION"
    PERSIST_SESSION = "PERSIST_SESSION"


class QueryResponseDeliveryType(str, Enum):
    """Query response delivery types in SQL Workbench API"""
    ASYNC = "ASYNC"
    SYNC = "SYNC"


@unique
class Language(Enum):
    def __new__(cls, value, supporting_connections):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._supporting_connections = supporting_connections
        return obj

    python = ("python", [CONNECTION_TYPE_SPARK_EMR_EC2,
                         CONNECTION_TYPE_SPARK_GLUE,
                         CONNECTION_TYPE_IAM,
                         CONNECTION_TYPE_SPARK_EMR_SERVERLESS])
    scala = ("scala", [CONNECTION_TYPE_SPARK_EMR_EC2,
                       CONNECTION_TYPE_SPARK_GLUE,
                       CONNECTION_TYPE_SPARK_EMR_SERVERLESS])
    sql = ("sql", [CONNECTION_TYPE_ATHENA,
                   CONNECTION_TYPE_REDSHIFT,
                   CONNECTION_TYPE_SPARK_EMR_EC2,
                   CONNECTION_TYPE_SPARK_GLUE,
                   CONNECTION_TYPE_SPARK_EMR_SERVERLESS])

    def supports_connection_type(self, connection_type: str) -> bool:
        if connection_type in self._supporting_connections:
            return True
        return False
