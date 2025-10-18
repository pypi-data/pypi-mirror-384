import json
import sys
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils

CREDENTIAL_PROCESS_FILE_NAME = "/credential_process_script.py"

def refresh_credential(connection_id: str):
    connection_detail = SageMakerToolkitUtils.get_connection_detail_from_id(connection_id, True)

    access_key_id = connection_detail["connectionCredentials"]["accessKeyId"]
    secret_access_key = connection_detail["connectionCredentials"]["secretAccessKey"]
    session_token = connection_detail["connectionCredentials"]["sessionToken"]
    expiration = connection_detail["connectionCredentials"]["expiration"]
    iso_expiration = expiration.isoformat()

    credential = {"Version" : 1,
                "AccessKeyId" : access_key_id,
                "SecretAccessKey" : secret_access_key,
                "SessionToken" : session_token,
                "Expiration" : iso_expiration
                }

    json_string = json.dumps(credential, indent=4)
    print(json_string)


def main():
    if len(sys.argv) < 2:
        print("Usage: python credential_process_script.py <connection_name>")
        sys.exit(1)
    connection_id = sys.argv[1]
    refresh_credential(connection_id)

if __name__ == "__main__":
    main()