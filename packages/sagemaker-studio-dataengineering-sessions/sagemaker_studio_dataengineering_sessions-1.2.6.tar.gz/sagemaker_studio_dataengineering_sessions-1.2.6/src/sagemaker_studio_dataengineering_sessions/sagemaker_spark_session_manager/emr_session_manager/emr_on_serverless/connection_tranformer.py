from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import ConnectionDetailError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_connection import \
    EmrOnServerlessConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    CONFIGURATION_NAME_SPARK_CONFIGURATIONS


def get_emr_on_serverless_connection(connection_name: str) -> EmrOnServerlessConnection:
    connection_details = SageMakerToolkitUtils.get_connection_detail(connection_name, True)
    connection_name = connection_details["name"]
    connection_id = connection_details["connectionId"]
    region = connection_details["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkEmrProperties", "livyEndpoint"]):
        livy_endpoint = connection_details["props"]["sparkEmrProperties"]["livyEndpoint"]
    else:
        raise ConnectionDetailError("Cannot get livy endpoint from connection")

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkEmrProperties", "runtimeRole"]):
        runtime_role = connection_details["props"]["sparkEmrProperties"]["runtimeRole"]
    else:
        raise ConnectionDetailError("Cannot get runtime role from connection")

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkEmrProperties", "computeArn"]):
        application_id = connection_details["props"]["sparkEmrProperties"]["computeArn"].split("/")[-1]
    else:
        raise ConnectionDetailError("Cannot get computeArn from connection")

    spark_configs = {}
    if "configurations" in connection_details and type(connection_details["configurations"]) == list:
        for config in connection_details["configurations"]:
            if config["classification"] == CONFIGURATION_NAME_SPARK_CONFIGURATIONS:
                spark_configs = config["properties"]

    return EmrOnServerlessConnection(connection_name=connection_name,
                                     connection_id=connection_id,
                                     url=livy_endpoint,
                                     runtime_role=runtime_role,
                                     application_id=application_id,
                                     spark_configs= spark_configs,
                                     region=region)


