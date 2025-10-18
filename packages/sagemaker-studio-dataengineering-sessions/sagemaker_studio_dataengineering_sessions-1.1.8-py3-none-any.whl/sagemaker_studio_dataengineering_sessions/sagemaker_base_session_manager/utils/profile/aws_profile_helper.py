import logging
import os
import subprocess

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import METADATA_CONTENT
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.utils.profile import credential_process_script
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.utils.profile.credential_process_script import CREDENTIAL_PROCESS_FILE_NAME

logger = logging.getLogger(__name__)

def create_aws_profile_if_not_existent(connection_id: str):
    logger.info(f"Creating aws profile for connection id: {connection_id} if not exists")
    aws_configuration_var_name = "credential_process"
    path = os.path.dirname(credential_process_script.__file__) + CREDENTIAL_PROCESS_FILE_NAME
    command = f'python {path} {connection_id}'
    if not _aws_profile_config_exist(profile_name=connection_id,
                                     config_variable=aws_configuration_var_name,
                                     command=command):
        if not _set_aws_profile_config_successfully(profile_name=connection_id,
                                                    config_variable=aws_configuration_var_name,
                                                    command=command):
            # If anything is wrong when setting up the profile, we will return early
            return


def set_aws_profile_and_region(profile_name: str, region: str | None):
    logger.info(f"Setting AWS profile to {profile_name}")
    os.environ["AWS_PROFILE"] = profile_name

    # need to set both AWS_REGION and AWS_DEFAULT_REGION because both are used.
    # AWS_REGION is used in AWS CLI
    # AWS_DEFAULT_REGION is used in boto3
    # ref: https://docs.aws.amazon.com/sdkref/latest/guide/feature-region.html#feature-region-sdk-compat
    if region:
        os.environ["AWS_REGION"] = region
        os.environ["AWS_DEFAULT_REGION"] = region


def reset_aws_profile_and_region():
    logger.info(f"Resetting AWS profile.")
    if "AWS_PROFILE" in os.environ:
        del os.environ["AWS_PROFILE"]
    # need to set both AWS_REGION and AWS_DEFAULT_REGION because both are used.
    # AWS_REGION is used in AWS CLI
    # AWS_DEFAULT_REGION is used in boto3
    # ref: https://docs.aws.amazon.com/sdkref/latest/guide/feature-region.html#feature-region-sdk-compat
    if METADATA_CONTENT and 'ResourceArn' in METADATA_CONTENT and len(METADATA_CONTENT['ResourceArn'].split(':')) >= 4:
        region = METADATA_CONTENT['ResourceArn'].split(':')[3]
        logger.info(f"Resetting AWS region to {region}.")
        os.environ["AWS_REGION"] = region
        os.environ["AWS_DEFAULT_REGION"] = region
    else:
        logger.warning("Unable to find ENV_REGION in environment variables. Skipping AWS_REGION reset.")


def _aws_profile_config_exist(profile_name, config_variable, command) -> bool:
    try:
        # Trying to get a specific configuration setting for the specified profile
        result = subprocess.run(['aws', 'configure', 'get', config_variable, '--profile', profile_name],
                                capture_output=True, text=True, check=True)
        if result.stdout.strip() == command:
            return True
        return False
    except subprocess.CalledProcessError:
        # This means the command failed (likely the profile does not exist)
        return False


def _set_aws_profile_config_successfully(profile_name, command, config_variable) -> bool:
    try:
        logger.info(f"Setting AWS profile: {profile_name}")
        set_command = ['aws', 'configure', 'set', config_variable, command, '--profile', profile_name]
        subprocess.run(set_command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting profile for: {profile_name}. Error: {e}")
        return False
