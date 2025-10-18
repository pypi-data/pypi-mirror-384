from logging import Logger

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import (
    ConnectionDetailError,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import (
    SageMakerConnectionDisplay,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import (
    SageMakerToolkitUtils,
)
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.athena.athena_connection import (
    AthenaConnection,
)


def get_athena_connection(connection_name: str, logger: Logger) -> AthenaConnection:
    connection_details = SageMakerToolkitUtils.get_connection_detail(connection_name, False)

    try:
        region = connection_details["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
    except KeyError:
        region = None
        SageMakerConnectionDisplay.write_msg(
            "Athena connection does not have AWS Region. Not setting it for connection"
        )
        logger.warning("Athena connection does not have AWS Region. Not setting it for connection")

    account_id = connection_details["physicalEndpoints"][0]["awsLocation"]["awsAccountId"]
    if "enableTrustedIdentityPropagation" in connection_details["physicalEndpoints"][0]:
        enable_tip = connection_details["physicalEndpoints"][0]["enableTrustedIdentityPropagation"]
    else:
        enable_tip = False

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_details, ["props", "athenaProperties", "workgroupName"]
    ):
        work_group = connection_details["props"]["athenaProperties"]["workgroupName"]
    else:
        raise ConnectionDetailError("Athena connection does not have workgroup name.")

    return AthenaConnection(
        connection_name=connection_details["name"],
        connection_id=connection_details["connectionId"],
        work_group=work_group,
        region=region,
        account_id=account_id,
        enable_tip=enable_tip,
    )
