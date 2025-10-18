import time

import sparkmagic.utils.configuration as conf
from sparkmagic.auth.customauth import Authenticator
from sparkmagic.utils.sparklogger import SparkLog

from boto3 import session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import json
import os
import re


SERVICE_NAME = "emr-serverless"
AWS_REGION = "AWS_REGION"
AWS_DEFAULT_REGION = "AWS_DEFAULT_REGION"
DEFAULT_EXECUTION_ROLE_ENV = "EMR_SERVERLESS_SESSION_RUNTIME_ROLE_ARN"
USE_USERNAME_AS_AWS_PROFILE_ENV = "USERNAME_AS_AWS_PROFILE"

class RuntimeRoleNotFoundException(Exception):
    pass

# This authenticator is identical to
# https://code.amazon.com/packages/AwsToledoSparkmagicAuthenticator/blobs/mainline/--/emr_serverless_customauth/customauthenticator.py
# Except it can take an extra attribute called signing_profile
# which specify the AWS_PROFILE credential to use when signing the request
class EMRServerlessCustomSigV4Signer(Authenticator):
    """Custom authenticator for SparkMagic
     1. read the creds using botocore
     2. calculate the SigV4 signature
     3. and add required headers to the request.
    """

    def __init__(self, parsed_attributes=None):
        """Initializes the Authenticator with the attributes in the attributes
        parsed from a %spark magic command if applicable, or with default values
        otherwise.

        Args:
            self,
            parsed_attributes (IPython.core.magics.namespace): The namespace object that
            is created from parsing %spark magic command.
        """
        Authenticator.__init__(self, parsed_attributes)
        self.logger = SparkLog("EMRServerlessSigV4Auth")
        if parsed_attributes is not None:
            url = parsed_attributes.__dict__["url"]
            self.user = parsed_attributes.user
        else:
            url = ""
            self.user = ""
        self.region = self.get_aws_region(url)
        self.default_role_arn = self.get_default_role_arn()
        use_user_as_profile_name = os.environ.get(USE_USERNAME_AS_AWS_PROFILE_ENV, '').lower()
        if self.user is not None and self.user and use_user_as_profile_name == 'true':
            self.boto_session = session.Session(profile_name=self.user)
            self.logger.info(f"Boto session created using profile: {self.user}")
        else:
            self.boto_session = session.Session()
            self.logger.info(f"Boto session created using default credential")

    def add_sigv4_auth(self, request):
        """
        Adds the Sigv4 signature to the request payload using the credentials available.
        """
        start_time = time.time()
        credentials = self.boto_session.get_credentials().get_frozen_credentials()

        try:
            aws_signer = SigV4Auth(credentials, SERVICE_NAME, self.region)
            payload = request.body
            http_method = request.method
            orig_headers = request.headers
            aws_headers = {
                "Content-Type": orig_headers.get("Content-Type", 'application/json')
            }
            aws_request = AWSRequest(method=http_method,
                                 url=request.url,
                                 data=payload,
                                 headers=aws_headers)
            aws_signer.add_auth(aws_request)

            for key in aws_request.headers.keys():
                value = aws_request.headers.get(key)

                request.headers[key] = value
        except Exception as err:
            self.logger.error(f"Unexpected {err=}, {type(err)=}")
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            self.logger.info(f"signing time {execution_time:.6f} seconds")

    def add_defaults_to_body(self, request):
        """
        Adds the default execution role to create session request body.
        """
        try:
            body = json.loads(request.body)
            if "conf" not in body:
                body["conf"] = {}
            session_execution_role = body["conf"].get("emr-serverless.session.executionRoleArn", self.default_role_arn)
            if session_execution_role is None:
                raise RuntimeRoleNotFoundException("Execution role arn is missing. Set the environment variable " +
                    f"{DEFAULT_EXECUTION_ROLE_ENV} or specify emr-serverless.session.executionRoleArn via the %%configure magic")
            body["conf"]["emr-serverless.session.executionRoleArn"] = session_execution_role
            self.logger.info("Session execution role resolved to " + session_execution_role)
            request.body = json.dumps(body)
        except RuntimeRoleNotFoundException as ex:
            raise
        except Exception as err:
            self.logger.error(f"Unable to set defaults, unexpected error. {err=}, {type(err)=}")

    def __call__(self, request):
        if request.method == "POST" and request.url.endswith("/sessions"):
            self.add_defaults_to_body(request)
        self.add_sigv4_auth(request)

        return request

    def __hash__(self):
        return hash((self.url, self.user, self.__class__.__name__))

    def get_aws_region(self, url) -> str:
        url_pattern = r".*\.livy.emr-serverless-services.*\.([a-z0-9-]+)\.amazonaws.com"
        matcher = re.match(url_pattern, url)
        default_region = "us-west-2"
        if matcher:
            region = matcher.group(1)
        else:
            region = os.getenv(AWS_REGION, os.getenv(AWS_DEFAULT_REGION, default_region))
        self.logger.info("AWS region resolved to " + region)
        return region

    def get_default_role_arn(self) -> str:
        if DEFAULT_EXECUTION_ROLE_ENV in os.environ:
            return os.getenv(DEFAULT_EXECUTION_ROLE_ENV)
        elif "emr-serverless.session.executionRoleArn" in conf.d:
            return conf.d["emr-serverless.session.executionRoleArn"]
        else :
            self.logger.debug("Default execution role not provided")
            return None
