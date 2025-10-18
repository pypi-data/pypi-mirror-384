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
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.redshift_connection import (
    RedshiftConnection,
)

AUTH_TYPE_SECRET_MANAGER = "SECRETS_MANAGER"
AUTH_TYPE_FEDERATED = "FEDERATED"


def get_redshift_connection(connection_name: str, logger: Logger) -> RedshiftConnection:
    connection_no_secret = SageMakerToolkitUtils.get_connection_detail(connection_name, False)

    try:
        region = connection_no_secret["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
    except KeyError:
        region = None
        SageMakerConnectionDisplay.write_msg(
            "Redshift connection does not have AWS Region. Not setting it for connection"
        )
        logger.warning("Redshift connection does not have AWS Region. Not setting it for connection")

    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_no_secret, ["props", "redshiftProperties", "credentials"]
    ) or SageMakerToolkitUtils.has_key_chain_in_connection_detail(  # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
        connection_no_secret, ["props", "jdbcProperties", "credentials"]
    ):
        auth_type = AUTH_TYPE_SECRET_MANAGER
    else:
        auth_type = AUTH_TYPE_FEDERATED


    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_no_secret, ["props", "redshiftProperties", "credentials", "secretArn"]
    ):
        secret_arn = connection_no_secret["props"]["redshiftProperties"]["credentials"]["secretArn"]
    else:
        secret_arn = None

    # get the database name from jdbcUrl
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_no_secret, ["props", "redshiftProperties", "jdbcUrl"]
    ):
        database = connection_no_secret["props"]["redshiftProperties"]["jdbcUrl"].split("/")[-1]
    # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
    elif SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_no_secret, ["props", "jdbcProperties", "jdbcUrl"]
    ):
        database = connection_no_secret["props"]["jdbcProperties"]["jdbcUrl"].split("/")[-1]
    else:
        raise ConnectionDetailError("Cannot get database name from jdbcUrl")

    account_id = connection_no_secret["physicalEndpoints"][0]["awsLocation"]["awsAccountId"]
    if "enableTrustedIdentityPropagation" in connection_no_secret["physicalEndpoints"][0]:
        enable_tip = connection_no_secret["physicalEndpoints"][0]["enableTrustedIdentityPropagation"]
    else:
        enable_tip = False

    return RedshiftConnection(
        connection_name=connection_no_secret["name"],
        connection_id=connection_no_secret["connectionId"],
        host=connection_no_secret["physicalEndpoints"][0]["host"],
        database=database,
        port=connection_no_secret["physicalEndpoints"][0]["port"],
        auth_type=auth_type,
        secret_arn=secret_arn,
        account_id=account_id,
        region=region,
        enable_tip=enable_tip,
    )


def get_redshift_connection_credentials(connection_id: str) -> tuple[str, str]:
    connection_detail = SageMakerToolkitUtils.get_connection_detail_from_id(connection_id, True)
    if SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_detail,
        ["props", "redshiftProperties", "credentials", "usernamePassword", "username"],
    ) and SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_detail,
        ["props", "redshiftProperties", "credentials", "usernamePassword", "password"],
    ):
        username = connection_detail["props"]["redshiftProperties"]["credentials"]["usernamePassword"]["username"]
        password = connection_detail["props"]["redshiftProperties"]["credentials"]["usernamePassword"]["password"]
        return username, password
    # TODO: to work with jdbcProperties, to be deleted after jdbcProperties goes away
    elif SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_detail,
        ["props", "jdbcProperties", "credentials", "usernamePassword", "username"],
    ) and SageMakerToolkitUtils.has_key_chain_in_connection_detail(
        connection_detail,
        ["props", "jdbcProperties", "credentials", "usernamePassword", "password"],
    ):
        username = connection_detail["props"]["jdbcProperties"]["credentials"]["usernamePassword"]["username"]
        password = connection_detail["props"]["jdbcProperties"]["credentials"]["usernamePassword"]["password"]
        return username, password
    else:
        raise ConnectionDetailError("Redshift connection detail does not contain credentials when expected")
