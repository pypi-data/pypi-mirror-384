import os
import boto3
from botocore.config import Config
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_kernel_utils.GlueSessionsConstants import *


def create_sts_client(profile=None, region=None, endpoint_url=None):
    if not region:
        raise ValueError(f"Region must be set.")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if not endpoint_url:
        return session.client(
            "sts",
            region_name=region,
            endpoint_url=_get_sts_endpoint_url(region),
        )
    else:
        return session.client(
            "sts",
            region_name=region,
            endpoint_url=endpoint_url,
        )


def create_iam_client(profile=None, region=None):
    if not region:
        raise ValueError(f"Region must be set.")
    if profile:
        return boto3.Session(profile_name=profile).client(
            "iam", region_name=region
        )
    else:
        return boto3.Session().client(
            "iam",
            region_name=region
        )


def create_s3_client(profile=None, region=None):
    if not region:
        raise ValueError(f"Region must be set.")
    if profile:
        return boto3.Session(profile_name=profile).client(
            "s3", region_name=region,
            config=Config(retries=dict(max_attempts=10))
        )
    else:
        return boto3.Session().client(
            "s3",
            region_name=region,
            config=Config(retries=dict(max_attempts=10))
        )


def create_glue_client(profile=None, region=None, endpoint_url=None):
    if not region:
        raise ValueError(f"Region must be set.")
    os.environ['AWS_DATA_PATH'] = _get_aws_model_dir()
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if not endpoint_url:
        return session.client("glue", region_name=region)
    else:
        return session.client("glue", region_name=region, endpoint_url = endpoint_url)

def create_emr_client(profile=None, region=None, endpoint_url=None):
    if not region:
        raise ValueError(f"Region must be set.")
    os.environ['AWS_DATA_PATH'] = _get_aws_model_dir()
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if not endpoint_url:
        return session.client("emr", region_name=region)
    else:
        return session.client("emr", region_name=region, endpoint_url = endpoint_url)
    

def create_sql_workbench_client(profile=None, region=None, endpoint_url=None):
    if not region:
        raise ValueError(f"Region must be set.")
    os.environ['AWS_DATA_PATH'] = _get_aws_model_dir()
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if not endpoint_url:
        return session.client("sqlworkbench", region_name=region)
    else:
        return session.client("sqlworkbench", region_name=region, endpoint_url=endpoint_url)


def create_emr_serverless_client(profile=None, region=None):
    if not region:
        raise ValueError(f"Region must be set.")
    if profile:
        return boto3.Session(profile_name=profile).client(
            "emr-serverless", region_name=region
        )
    else:
        return boto3.Session().client(
            "emr-serverless",
            region_name=region)


def create_sagemaker_client(profile=None, region=None, endpoint_url=None):
    if not region:
        raise ValueError(f"Region must be set.")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if not endpoint_url:
        return session.client("sagemaker", region_name=region)
    else:
        return session.client("sagemaker", region_name=region, endpoint_url=endpoint_url)


def _get_sts_endpoint_url(region):
    if region in CHINA_REGIONS:
        return f"https://sts.{region}.amazonaws.com.cn"
    return f"https://sts.{region}.amazonaws.com"


def _get_aws_model_dir():
    # This is used to configure AWS_DATA_PATH value for additional directories to check for AWS CLI.
    # https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html
    # TODO: remove datazone and glue until boto version is up to date in SMD
    # sqlworkbench directory should be retained for RedShift usecase.
    try:
        import sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager
        path = os.path.dirname(sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.__file__)
        return path + "/boto3_models"
    except ImportError:            
        raise RuntimeError("Unable to import sagemaker_base_session_manager, thus cannot initialize datazone client.")
