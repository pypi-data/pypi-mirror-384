import json

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (Language, DATAZONE_DOMAIN_REGION, DATAZONE_ENVIRONMENT_ID,
                                                           DATAZONE_ENDPOINT_URL, DATAZONE_STAGE, DOMAIN_ID,
                                                           PROJECT_ID, PROJECT_S3_PATH)
from pandas import DataFrame


def send_dict_to_spark_command(local_value: dict, remote_var_name: str, language: Language) -> str:
    if language == Language.python:
        return _send_dict_to_spark_command_python(local_value, remote_var_name)
    else:
        raise NotImplementedError("cannot send python dict to remote spark in language other than python")


def send_str_to_spark_command(local_value: str, remote_var_name: str, language: Language) -> str:
    if language == Language.python:
        return _send_str_to_spark_command_python(local_value, remote_var_name)
    elif language == Language.scala:
        return _send_str_to_spark_command_scala(local_value, remote_var_name)
    else:
        raise NotImplementedError(f"cannot send string to remote spark in language {language.name}")


def send_pandas_df_to_spark_command(local_value: DataFrame, remote_var_name: str, language: Language) -> str:
    if language == Language.python:
        return _send_pandas_df_to_spark_command_python(local_value, remote_var_name)
    elif language == Language.scala:
        return _send_pandas_df_to_spark_command_scala(local_value, remote_var_name)

def send_datazone_metadata_command(language: Language) -> str:
    if language == Language.python:
        # Only send metadata if language is python
        # env var name should be aligned with training job definition
        # https://code.amazon.com/packages/MaxDomePythonSDK/blobs/6d10ae586b2bc46ad60474e78f9890cb465de451/--/src/maxdome/execution/remote_execution_client.py#L397-L403
        return f'''try:
  import os
  os.environ["DataZoneDomainRegion"] = "{DATAZONE_DOMAIN_REGION}"
  os.environ["DataZoneDomainId"] = "{DOMAIN_ID}"
  os.environ["DataZoneProjectId"] = "{PROJECT_ID}"
  os.environ["DataZoneEnvironmentId"] = "{DATAZONE_ENVIRONMENT_ID}"
  os.environ["DataZoneStage"] = "{DATAZONE_STAGE}"
  os.environ["DataZoneEndpoint"] = "{DATAZONE_ENDPOINT_URL}"
  os.environ["ProjectS3Path"] = "{PROJECT_S3_PATH}"
except Exception:
  pass'''

def _send_dict_to_spark_command_python(local_value: dict, remote_var_name: str) -> str:
    # dict
    temp_json = repr(json.dumps(local_value))
    # cannot have indents to make sure the command is valid when sending to spark
    return f"""import json
remote_json = {temp_json}
{remote_var_name}=json.loads(remote_json)"""


def _send_str_to_spark_command_python(local_value: str, remote_var_name: str) -> str:
    return f"{remote_var_name} = {repr(local_value)}"


def _send_str_to_spark_command_scala(local_value: str, remote_var_name: str) -> str:
    return f'var {remote_var_name} = """{local_value}"""'


def _send_pandas_df_to_spark_command_python(local_value: DataFrame, remote_var_name: str) -> str:
    pandas_json = local_value.to_json(orient='records')
    return f"""import json
import pandas
json_pandas_df = json.loads('{pandas_json}')
{remote_var_name} = spark.createDataFrame(pandas.DataFrame(json.loads('{pandas_json}')))"""


def _send_pandas_df_to_spark_command_scala(local_value: DataFrame, remote_var_name: str) -> str:
    pandas_json = local_value.to_json(orient='records')
    # this does not work when LakeFormation is enabled, because RDD is used
    return f'''val {remote_var_name} = spark.read.json(Seq("""{pandas_json}""").toDS)'''
