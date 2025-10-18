import logging
import os
import ssl
from ssl import SSLError

import requests
import urllib3
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import create_emr_client
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_gateway import EmrGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.s3_gateway import S3Gateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import AuthenticationError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.connection_transformer import \
    get_emr_on_ec2_connection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_debugging_helper import EmrOnEc2DebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.governance_type import GovernanceType
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.livy_session import LivySession, AUTHENTICATOR
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_monitor_widget_utils import add_session_info_in_user_ns, clear_current_connection_in_user_ns
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import CONNECTION_TYPE_SPARK_EMR_EC2
from sparkmagic.livyclientlib.endpoint import Endpoint
from sparkmagic.livyclientlib.exceptions import HttpClientException
from sparkmagic.utils.constants import AUTH_BASIC, NO_AUTH
from requests.utils import DEFAULT_CA_BUNDLE_PATH

from sparkmagic.utils.utils import initialize_auth, Namespace
import sparkmagic.utils.configuration as conf

from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.common_utils import apply_compatibility_mode_configs

AUTH_ERROR_MESSAGE = "Invalid status code '403' from"
SUFFIX_PEM_LOCATION = "/sys/emr/certs/trustedCertificates.pem"
TEMP_PEM_DIR = os.path.expanduser('~/.tmp_pem')
TEMP_PEM_FILE_PATH = TEMP_PEM_DIR + "/temp.pem"
SAGEMAKER_EMR_EC2_TRUSTED_CA_COMMENT = "# SageMaker connection trusted certificate for :"


class EmrOnEc2Session(LivySession):
    auto_add_catalogs = False
    logger = logging.getLogger(__name__)

    def __init__(self, connection_name: str):
        # The connection_details are required to get the profile, which is needed for super.__init__
        self.connection_details = get_emr_on_ec2_connection(connection_name)
        super().__init__(connection_name)
        self.connection_type = CONNECTION_TYPE_SPARK_EMR_EC2
        self.s3_gateway = S3Gateway()
        self.emr_client = create_emr_client(self.profile, self.connection_details.region)
        self.emr_gateway = EmrGateway(self.emr_client)
        # s3 profile should always be default as we should use the project role to get the certs.
        self.debugging_helper = EmrOnEc2DebuggingHelper(gateway=self.emr_gateway, session=self)
        self.s3_gateway.initialize_clients(profile=None, s3_profile="default")
        conf.override(conf.authenticators.__name__, AUTHENTICATOR)
        if self.connection_details.governance_type == GovernanceType.USER_MANAGED:
            args = Namespace(
                connection_id=self.connection_details.connection_id,
                auth=NO_AUTH,
                url=self.connection_details.url,
            )
        else:
            args = Namespace(
                connection_id=self.connection_details.connection_id,
                auth=AUTH_BASIC,
                url=self.connection_details.url,
            )
        self.auth = initialize_auth(args)

    def create_livy_endpoint(self):
        # If the auth is NO_AUTH, then self.auth should be None
        if not self.auth:
            return Endpoint(self.connection_details.url, self.auth)

        self.auth.refresh_credentials()
        return Endpoint(self.connection_details.url, self.auth)

    def _is_fta_supported(self):
        return False

    def handle_exception(self, e: Exception):
        if isinstance(e, HttpClientException) and AUTH_ERROR_MESSAGE in str(e) and self.auth:
            self.auth.refresh_credentials()
            raise AuthenticationError("Authentication failed. Please try rerun the cell.")
        else:
            raise e
        
    def _apply_compatibility_mode_configs(self):
        self.get_logger().info(f"Applying compatibility mode configs for EMR EC2 cluster {self.connection_details.cluster_id}")
        if self._is_fta_supported():
            self.config_dict["conf"] = apply_compatibility_mode_configs(self.config_dict["conf"])


    def configure_properties(self):
        self.config_dict.setdefault("conf", {})
        self._apply_compatibility_mode_configs()
        conf.override(conf.session_configs.__name__, self.config_dict)
        return conf.get_session_properties(self.language)

    def pre_session_creation(self):
        # disable warnings to make sure output is clean
        super().pre_session_creation()
        urllib3.disable_warnings()

        if not self.connection_details.trusted_certificates_s3_uri:
            self.get_logger().info("Will not download the trusted certificate from S3 because there is no path to a trusted cert.")
            return
        with open(DEFAULT_CA_BUNDLE_PATH, 'r') as ca_cert:
            content = ca_cert.read()
            if f"{SAGEMAKER_EMR_EC2_TRUSTED_CA_COMMENT} {self.connection_details.connection_id}" in content:
                self.get_logger().info("The trusted certificate is already present on space")
                return
        self.get_logger().info("The trusted certificate is not present on space. downloading...")
        try:
            if not os.path.exists(TEMP_PEM_DIR):
                try:
                    os.makedirs(TEMP_PEM_DIR)
                except OSError:
                    self.get_logger().error(f"Failed to create temp dir {TEMP_PEM_DIR}. Skipping creating temp dir and continue")
            bucket_name, object_key = (self.connection_details.trusted_certificates_s3_uri[5:]
                                       .split('/', 1))
            self.s3_gateway.download_from_s3(bucket_name, object_key, TEMP_PEM_FILE_PATH)
            with open(TEMP_PEM_FILE_PATH, "r") as source_file:
                with open(DEFAULT_CA_BUNDLE_PATH, "a") as destination_file:
                    destination_file.write(f"{SAGEMAKER_EMR_EC2_TRUSTED_CA_COMMENT} {self.connection_details.connection_id}\n")
                    lines = source_file.readlines()
                    destination_file.writelines(lines)
            self.get_logger().info(f"The trusted certificate is downloaded to {TEMP_PEM_FILE_PATH}")
            # REQUESTS_CA_BUNDLE is the default cert path, however we still need to
            # set REQUESTS_CA_BUNDLE to force reload the newly added content of DEFAULT_CA_BUNDLE_PATH.
            # Otherwise the newly added pem will not be loaded and verification will fail
            os.environ['REQUESTS_CA_BUNDLE'] = DEFAULT_CA_BUNDLE_PATH
            exc = self._surface_verify_ssl_error()
            if exc is None:
                self.get_logger().info("Certificate verification for HTTPS succeeded.")
            elif isinstance(exc, requests.exceptions.SSLError) or isinstance(
                exc, ssl.SSLError
            ):
                SageMakerConnectionDisplay.send_error(f"Certificate verification for HTTPS request failed. "
                                                    f"Error: [{exc.__class__.__name__}: {exc}]")

        except Exception as e:
            self.get_logger().warning(f"Unable to configure the trusted certificate from S3 because of error: {e.__class__.__name__}: {e}\n Skipping")
        finally:
            try:
                os.remove(TEMP_PEM_FILE_PATH)
            except Exception as e:
                self.get_logger().info(f"Unable to remove the temporary PEM file: {e.__class__.__name__}: {e}")
                pass

    def pre_run_statement(self):
        clear_current_connection_in_user_ns()
        app_id = self.spark_magic.spark_controller.get_app_id(self.connection_name)
        add_session_info_in_user_ns(connection_name=self.connection_name, connection_type=CONNECTION_TYPE_SPARK_EMR_EC2,
                                    application_id=app_id)
        self.get_logger().info(f"Spark App id: {app_id}")


    def _install_from_pip(self) -> any:
        if self.lib_provider.get_pypi_modules():
            SageMakerConnectionDisplay.write_msg("Installing python packages from pip.")
            for lib in self.lib_provider.get_pypi_modules():
                self.run_statement(cell=f"sc.install_pypi_package('{lib}')")

    def _surface_verify_ssl_error(self):
        """
        _surface the error to the user if there will be SSL errors.
        :return:
        """
        try:
            requests.get(self.connection_details.url, verify=True)
        except (SSLError, requests.exceptions.SSLError, OSError, Exception) as e:
            """
            Also catch generic "Exception" so that this code path doesn't fail execution. Most likely, the same Exception will
            also be raised when we try to actually connect to execute the connection to given host:port. Relegate failure to that code path.
            """
            return e

        return None

    def _set_libs(self, properties):
        self.lib_provider.refresh()
        # Add jar
        if self.lib_provider.get_maven_artifacts():
            properties.setdefault("conf", {})
            properties["conf"].setdefault("spark.jars.packages", ",".join(self.lib_provider.get_maven_artifacts()))
        if (self.lib_provider.get_local_java_libs() or self.lib_provider.get_other_java_libs()
                or self.lib_provider.get_s3_java_libs()):
            properties.setdefault("conf", {})
            properties["conf"].setdefault("spark.jars", ",".join(self.lib_provider.get_local_java_libs()
                                                                 + self.lib_provider.get_other_java_libs()
                                                                 + self.lib_provider.get_s3_java_libs()))

        # Add python
        if self.lib_provider.get_archive():
            # If archive is specified, Skip all other python lib config.
            properties.setdefault("conf", {})
            config = properties["conf"]
            config.setdefault("spark.pyspark.python", "./environment/bin/python")
            config.setdefault("spark.archives", self.lib_provider.get_archive() + "#environment")
        else:
            if (self.lib_provider.get_local_python_libs() or self.lib_provider.get_other_python_libs()
                    or self.lib_provider.get_s3_python_libs()):
                properties.setdefault("pyFiles", (self.lib_provider.get_local_python_libs()
                                                  + self.lib_provider.get_other_python_libs()
                                                  + self.lib_provider.get_s3_python_libs()))
            if self.lib_provider.get_pypi_modules():
                properties.setdefault("conf", {})
                config = properties["conf"]
                config.setdefault("spark.pyspark.python", "python3")
                config.setdefault("spark.pyspark.virtualenv.enabled", "true")
                config.setdefault("spark.pyspark.virtualenv.type", "native")
                config.setdefault("spark.pyspark.virtualenv.bin.path", "/usr/bin/virtualenv")

    def _lakeformation_session_level_setting_supported(self) -> bool:
        return False
