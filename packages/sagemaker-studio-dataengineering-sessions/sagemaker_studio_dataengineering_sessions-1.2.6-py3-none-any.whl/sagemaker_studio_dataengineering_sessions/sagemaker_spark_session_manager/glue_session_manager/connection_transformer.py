from logging import Logger

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (CONFIGURATION_NAME_GLUE_DEFAULT_ARGUMENTS,
                                                                                                       CONFIGURATION_NAME_SPARK_CONFIGURATIONS,
                                                                                                       CONNECTION_TYPE_REDSHIFT, PROJECT_ID, EXECUTION_ROLE_ARN)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import ConnectionDetailError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_connection import GlueConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.common_utils import apply_compatibility_mode_configs

def get_glue_connection(connection_name: str, logger: Logger) -> GlueConnection:
    connection_details = SageMakerToolkitUtils.get_connection_detail(connection_name, True)
    name = connection_details["name"]
    connection_id = connection_details["connectionId"]
    region = connection_details["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
    account_id = connection_details["physicalEndpoints"][0]["awsLocation"]["awsAccountId"]
    project = PROJECT_ID

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_details, ["environmentUserRole"]):
        glue_iam_role = connection_details["environmentUserRole"]
    else:
        glue_iam_role = EXECUTION_ROLE_ARN

    if not glue_iam_role:
        raise ConnectionDetailError("Cannot get Glue IAM role from connection details")

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkGlueProperties", "glueConnectionName"]):
        glue_connection = connection_details["props"]["sparkGlueProperties"]["glueConnectionName"]
    else:
        glue_connection = None

    session_configs = {}
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkGlueProperties", "glueVersion"]):
        session_configs["glue_version"] = connection_details["props"]["sparkGlueProperties"]["glueVersion"]
    else:
        session_configs["glue_version"] = "4.0"

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkGlueProperties", "idleTimeout"]):
        session_configs["idle_timeout"] = connection_details["props"]["sparkGlueProperties"]["idleTimeout"]
    else:
        session_configs["idle_timeout"] = 60

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkGlueProperties", "numberOfWorkers"]):
        session_configs["number_of_workers"] = connection_details["props"]["sparkGlueProperties"]["numberOfWorkers"]
    else:
        session_configs["number_of_workers"] = 10

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkGlueProperties", "workerType"]):
        session_configs["worker_type"] = connection_details["props"]["sparkGlueProperties"]["workerType"]
    else:
        session_configs["worker_type"] = "G.1X"

    default_arguments = {}
    # TODO: leverage the spark_configs when connection supports it
    spark_configs = {}
    if "configurations" in connection_details and type(connection_details["configurations"]) == list:
        for config in connection_details["configurations"]:
            if config["classification"] == CONFIGURATION_NAME_GLUE_DEFAULT_ARGUMENTS:
                default_arguments = config["properties"]
            if config["classification"] == CONFIGURATION_NAME_SPARK_CONFIGURATIONS:
                spark_configs = config["properties"]
    if default_arguments.get('--enable-lakeformation-fine-grained-access', 'false').lower() == 'false':
        session_configs["is_compatibility_mode"] = True

    related_redshift_properties = {}
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(connection_details, ["props", "sparkGlueProperties", "additionalArgs", "connection"]):
        related_connection_id = connection_details["props"]["sparkGlueProperties"]["additionalArgs"]["connection"]
        try:
            related_connection_details = SageMakerToolkitUtils.get_connection_detail_from_id(related_connection_id, True)
        except Exception as e:
            related_connection_details = None
            logger.warning(f"Unable to get related connection details because of {e.__class__.__name__}: {e}. "
                           f"Ignoring related connection in additionalArg.")
            SageMakerConnectionDisplay.write_msg(f"Unable to get related connection details because of "
                                               f"{e.__class__.__name__}: {e}. "
                                               f"Ignoring related connection in additionalArg.")

        if related_connection_details and related_connection_details["type"] == CONNECTION_TYPE_REDSHIFT:
            related_redshift_properties["connectionId"] = related_connection_id
            if SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["environmentUserRole"]):
                related_redshift_properties["iamRole"] = related_connection_details["environmentUserRole"]
            else:
                related_redshift_properties["iamRole"] = ""

            if SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "redshiftProperties", "redshiftTempDir"]):
                related_redshift_properties["redshiftTempDir"] = related_connection_details["props"]["redshiftProperties"]["redshiftTempDir"]
            # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
            elif SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "jdbcProperties", "redshiftTempDir"]):
                related_redshift_properties["redshiftTempDir"] = related_connection_details["props"]["jdbcProperties"]["redshiftTempDir"]
            else:
                related_redshift_properties["redshiftTempDir"] = ""

            if SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "redshiftProperties", "jdbcUrl"]):
                related_redshift_properties["jdbcUrl"] = related_connection_details["props"]["redshiftProperties"]["jdbcUrl"]
            # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
            elif SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "jdbcProperties", "jdbcUrl"]):
                related_redshift_properties["jdbcUrl"] = related_connection_details["props"]["jdbcProperties"]["jdbcUrl"]
            else:
                related_redshift_properties["jdbcUrl"] = ""

            if SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "redshiftProperties", "jdbcIamUrl"]):
                related_redshift_properties["jdbcIamUrl"] = related_connection_details["props"]["redshiftProperties"]["jdbcIamUrl"]
            # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
            elif SageMakerToolkitUtils.has_key_chain_in_connection_detail(related_connection_details, ["props", "jdbcProperties", "jdbcIamUrl"]):
                related_redshift_properties["jdbcIamUrl"] = related_connection_details["props"]["jdbcProperties"]["jdbcIamUrl"]
            else:
                related_redshift_properties["jdbcIamUrl"] = ""

        else:
            SageMakerConnectionDisplay.write_msg(f"The connection type in additionalArg of connection: {name} is not supported. Ignoring.")

    return GlueConnection(connection_name=name,
                          connection_id=connection_id,
                          region=region,
                          account=account_id,
                          project=project,
                          glue_connection=glue_connection,
                          session_configs=session_configs,
                          glue_iam_role=glue_iam_role,
                          default_arguments=default_arguments,
                          spark_configs=spark_configs,
                          related_redshift_properties=related_redshift_properties)
