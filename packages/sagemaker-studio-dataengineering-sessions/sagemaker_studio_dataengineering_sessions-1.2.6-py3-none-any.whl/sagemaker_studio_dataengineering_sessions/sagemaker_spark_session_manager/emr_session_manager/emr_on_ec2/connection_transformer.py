from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import ConnectionDetailError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_connection import EmrOnEc2Connection
from typing import Tuple

from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.governance_type import \
    GovernanceType

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    CONFIGURATION_NAME_SPARK_CONFIGURATIONS


def get_emr_on_ec2_connection(connection_name: str) -> EmrOnEc2Connection:
    connection_details = SageMakerToolkitUtils.get_connection_detail(connection_name, True)
    connection_name = connection_details["name"]
    connection_id = connection_details["connectionId"]
    region = connection_details["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(connection_details,
                                                              ["props", "sparkEmrProperties", "livyEndpoint"]):
        livy_endpoint = connection_details["props"]["sparkEmrProperties"]["livyEndpoint"]
    else:
        raise ConnectionDetailError("Cannot get livy endpoint from connection")

    trusted_certificates_s3_uri = ""
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkEmrProperties", "trustedCertificatesS3Uri"]):
        trusted_certificates_s3_uri = connection_details["props"]["sparkEmrProperties"]["trustedCertificatesS3Uri"]


    governance_type = GovernanceType.AWS_MANAGED
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(connection_details,
                                                              ["props", "sparkEmrProperties", "governanceType"]):
        governance_type_str = connection_details["props"]["sparkEmrProperties"]["governanceType"]
        if governance_type_str and governance_type_str == GovernanceType.USER_MANAGED.value:
            governance_type = GovernanceType.USER_MANAGED
    
    # TODO: once this SIM https://sim.amazon.com/issues/V1530843192 is resolved,
    # we should remove the default value logic, and error out if the governanceType is not in the response.

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(connection_details,
                                                              ["props", "sparkEmrProperties", "computeArn"]):
        cluster_id = connection_details["props"]["sparkEmrProperties"]["computeArn"].split("/")[-1]
    else:
        raise ConnectionDetailError("Cannot get cluster id from connection")

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(connection_details,
                                                              ["props", "sparkEmrProperties", "runtimeRole"]):
        runtime_role_arn = connection_details["props"]["sparkEmrProperties"]["runtimeRole"]
    else:
        runtime_role_arn = ""

    spark_configs = {}
    if "configurations" in connection_details and type(connection_details["configurations"]) == list:
        for config in connection_details["configurations"]:
            if config["classification"] == CONFIGURATION_NAME_SPARK_CONFIGURATIONS:
                spark_configs = config["properties"]

    # TODO: use spark_configs in EmrOnEc2Connection for storing default spark_configs
    return EmrOnEc2Connection(connection_name=connection_name,
                              connection_id=connection_id,
                              cluster_id = cluster_id,
                              runtime_role_arn = runtime_role_arn,
                              trusted_certificates_s3_uri=trusted_certificates_s3_uri,
                              url=livy_endpoint,
                              spark_configs=spark_configs,
                              governance_type=governance_type,
                              region=region)


def get_username_password(connection_id: str) -> Tuple[str, str]:
    connection_details = SageMakerToolkitUtils.get_connection_detail_from_id(connection_id, True)
    if (SageMakerToolkitUtils.has_key_chain_in_connection_detail(
            connection_details, ["props", "sparkEmrProperties", "credentials", "username"]) and
            SageMakerToolkitUtils.has_key_chain_in_connection_detail(
                connection_details, ["props", "sparkEmrProperties", "credentials", "password"])):
        username = connection_details["props"]["sparkEmrProperties"]["credentials"]["username"]
        password = connection_details["props"]["sparkEmrProperties"]["credentials"]["password"]
    else:
        raise ConnectionDetailError("Cannot get username and password from connection")
    return username, password
