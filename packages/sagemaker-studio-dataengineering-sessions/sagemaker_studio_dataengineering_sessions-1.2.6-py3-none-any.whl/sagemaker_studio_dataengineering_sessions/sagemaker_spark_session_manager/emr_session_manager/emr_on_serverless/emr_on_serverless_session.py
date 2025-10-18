import os
import time

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import SessionExpiredError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.release_label_utils import \
    compare_emr_release_labels
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.connection_tranformer import \
    get_emr_on_serverless_connection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.custom_authenticator import \
    USE_USERNAME_AS_AWS_PROFILE_ENV
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_serverless_gateway import \
    EmrServerlessGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_debugging_helper import EmrOnServerlessDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.livy_session import LivySession, AUTHENTICATOR
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_monitor_widget_utils import add_session_info_in_user_ns, \
    clear_current_connection_in_user_ns
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import CONNECTION_TYPE_SPARK_EMR_SERVERLESS, \
    IS_REMOTE_WORKFLOW, DOMAIN_ID, USER_ID, PROJECT_ID, CONFIGURATION_NAME_SPARK_DEFAULTS
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.common_utils import apply_compatibility_mode_configs

import sparkmagic.utils.configuration as conf
from sparkmagic.livyclientlib.endpoint import Endpoint
from sparkmagic.livyclientlib.exceptions import HttpClientException, SessionManagementException
from sparkmagic.utils.utils import initialize_auth, Namespace

WAIT_TIME = 1
TIME_OUT_IN_SECONDS = 105
APPLICATION_READY_TO_START_STATE = ["CREATED", "STOPPED"]
APPLICATION_TRANSIENT_STATE = ["STARTING", "STOPPING", "CREATING"]
APPLICATION_FINAL_STATE = ["CREATED", "STARTED", "STOPPED", "TERMINATED"]
APPLICATION_START_FAIL_STATE = ["TERMINATED", "STOPPING", "STOPPED"]
APPLICATION_STARTING_STATE = ["STARTING"]
APPLICATION_STARTED_STATE = ["STARTED"]
APPLICATION_NOT_STARTED_ERROR_MESSAGE = "Application must be started to access livy endpoint"
EMR_VERSION_SUPPORT_FOR_LAKEFORMATION = "emr-7.8.0"
EMR_VERSION_SUPPORT_FOR_OPENLINEAGE = "emr-7.5.0"
EMR_VERSION_SUPPORT_FOR_S3AG = "emr-6.15.0"

class EmrOnServerlessSession(LivySession):
    def __init__(self, connection_name: str):
        # The connection_details are required to get the profile, which is needed for super.__init__
        self.connection_details = get_emr_on_serverless_connection(connection_name)
        super().__init__(connection_name)
        self.connection_type = CONNECTION_TYPE_SPARK_EMR_SERVERLESS
        self.emr_serverless_gateway = EmrServerlessGateway(**self._get_profile_and_region())
        # set it as attribute to allow configuration from outside of the session
        self.time_out = TIME_OUT_IN_SECONDS
        emr_serverless_application = self.emr_serverless_gateway.get_emr_serverless_application(
 	        self.connection_details.application_id)
        self.release_label = emr_serverless_application['releaseLabel']
        self.debugging_helper = EmrOnServerlessDebuggingHelper(gateway=self.emr_serverless_gateway, session=self)
        self.is_compatibility_mode_enabled = self._is_compatibility_mode_enabled(emr_serverless_application)
        self.get_logger().info(f"Spark configs for EMR Serverless application {self.connection_details.application_id} is {self.connection_details.spark_configs}")
        
    def _apply_compatibility_mode_configs(self):
        if self._is_fta_supported():
            self.get_logger().info(f"Applying compatibility mode configs for EMR Serverless application {self.connection_details.application_id}")
        
            self.config_dict["conf"] = apply_compatibility_mode_configs(self.config_dict["conf"])

    def _is_compatibility_mode_enabled(self, emr_serverless_application):
        runtime_config = emr_serverless_application.get('runtimeConfiguration', None)
        if runtime_config is None:
            return False
        
        for config in runtime_config:
            if config.get("classification") == CONFIGURATION_NAME_SPARK_DEFAULTS:
                properties = config.get("properties", None)
                if properties is not None:
                    return properties.get('spark.emr-serverless.lakeformation.enabled', 'false').lower() == 'false'
                else:
                    return False
        return False
    
    def _is_fta_supported(self):
        self.get_logger().info(f"Checking if compatibility mode is enabled for EMR Serverless application {self.connection_details.application_id}, emr release label is {self.release_label}")
        is_supported_emr_release = compare_emr_release_labels(self.release_label, EMR_VERSION_SUPPORT_FOR_LAKEFORMATION) >= 0
        if self.is_compatibility_mode_enabled and is_supported_emr_release:
            return True
        return False

    def pre_session_creation(self):
        super().pre_session_creation()
        state = self.emr_serverless_gateway.get_emr_serverless_application_state(self.connection_details.application_id)
        self.get_logger().info(
            f"EMR Serverless application {self.connection_details.application_id} currently in state {state}")
        if state in APPLICATION_TRANSIENT_STATE:
            state = self._wait_until_application_status(waiting_status=APPLICATION_TRANSIENT_STATE,
                                                        target_status=APPLICATION_FINAL_STATE,
                                                        error_status=[])
        if state in APPLICATION_READY_TO_START_STATE:
            self.get_logger().info(f"Starting EMR Serverless application {self.connection_details.application_id}")
            SageMakerConnectionDisplay.write_msg(
                f"Starting EMR Serverless ({self.connection_details.application_id})")
            # Try to delete the session in case it is already managed by spark magic.
            try:
                self.app_id = None
                self.spark_magic.spark_controller.delete_session_by_name(self.connection_details.connection_name)
            except SessionManagementException as e:
                self.get_logger().info(f"Could not delete session named {self.connection_details.connection_name} because of {e}."
                                       f"This could be caused when spark magic spark controller does not contain such session. "
                                       f"This is expected when starting session for connection for the first time.")

            self.emr_serverless_gateway.start_emr_serverless_application(self.connection_details.application_id)
            state = self._wait_until_application_status(waiting_status=APPLICATION_STARTING_STATE,
                                                        target_status=APPLICATION_STARTED_STATE,
                                                        error_status=APPLICATION_START_FAIL_STATE)
        if state in APPLICATION_STARTED_STATE:
            SageMakerConnectionDisplay.write_msg(
                f"EMR Serverless ({self.connection_details.application_id}) is started")
            return
        else:
            raise RuntimeError(
                f"Application {self.connection_details.application_id} for {self.connection_name} reached illegal status {state}")

    def pre_run_statement(self):
        session = self._get_session()
        session_id = session.id
        clear_current_connection_in_user_ns()
        
        # Get YARN application ID (Job Run ID)
        try:
            if not self.app_id:
                self.app_id = self.spark_magic.spark_controller.get_app_id(self.connection_name)
            app_id = self.app_id
        except Exception as e:
            self.get_logger().warning(f"Could not get YARN app_id for EMR Serverless connection {self.connection_name}: {e}")
            app_id = None
        
        add_session_info_in_user_ns(connection_name=self.connection_name,
                                    connection_type=CONNECTION_TYPE_SPARK_EMR_SERVERLESS, 
                                    session_id=session_id,
                                    application_id=app_id)

    def create_livy_endpoint(self):
        conf.override(conf.authenticators.__name__, AUTHENTICATOR)
        os.environ[USE_USERNAME_AS_AWS_PROFILE_ENV] = "true"
        args = Namespace(
            auth="Custom_Auth",
            url=self.connection_details.url,
            user=self.connection_details.connection_id,
        )
        return Endpoint(self.connection_details.url, initialize_auth(args))

    def configure_properties(self) -> any:
        # EMR serverless requires emr-serverless.session.executionRoleArn to be in the post session request
        self.config_dict.setdefault("conf", {})
        self.config_dict["conf"].setdefault("emr-serverless.session.executionRoleArn", self.connection_details.runtime_role)
        if self._s3ag_supported():
            try:
                env = self.datazone_gateway.get_project_tooling_environment(project_id=PROJECT_ID)
                if self.datazone_gateway.is_s3_ag_enabled_for_environment(env):
                    self.config_dict["conf"].update({
                        "spark.hadoop.fs.s3.s3AccessGrants.enabled": "true",
                        "spark.hadoop.fs.s3.s3AccessGrants.fallbackToIAM": "true"
                    })
                    self.get_logger().info("S3 Access Grants enabled for Spark configuration")
            except Exception as e:
                self.logger.warning(f"Failed to check S3 AG status: {e}")
        if IS_REMOTE_WORKFLOW and self._openlineage_supported():
            openlineage_configs = {
                "spark.extraListeners": "io.openlineage.spark.agent.OpenLineageSparkListener",
                "spark.openlineage.transport.type": "amazon_datazone_api",
                "spark.openlineage.transport.domainId": DOMAIN_ID,
                "spark.glue.accountId": self.account_id,
            }
            self.config_dict["conf"].update(openlineage_configs)
        elif not IS_REMOTE_WORKFLOW and self._openlineage_supported():
            try:
                username = self.datazone_gateway.get_username(USER_ID)
            except Exception as e:
                self.logger.error(f"Failed to get username from DataZone: {e}")
                username = "unknown_user"
            openlineage_configs = {
                "spark.extraListeners": "io.openlineage.spark.agent.OpenLineageSparkListener",
                "spark.openlineage.transport.type": "amazon_datazone_api",
                "spark.openlineage.transport.domainId": DOMAIN_ID,
                "spark.glue.accountId": self.account_id,
                "spark.glue.JOB_NAME": f"Interactive/{PROJECT_ID}/{username}"
            }
            self.config_dict["conf"].update(openlineage_configs)
        
        self._apply_compatibility_mode_configs()
        conf.override(conf.session_configs.__name__, self.config_dict)
        return conf.get_session_properties(self.language)

    def handle_exception(self, e: Exception):
        if isinstance(e, HttpClientException) and APPLICATION_NOT_STARTED_ERROR_MESSAGE in str(e):
            self.session_started = False
            self.app_id = None
            sessions = self.spark_magic.spark_controller.session_manager.sessions
            if self.connection_details.connection_name in list(sessions):
                del sessions[self.connection_details.connection_name]
            raise SessionExpiredError("EMR Serverless application is stopped. Please rerun the cell to start the application.")
        else:
            raise e

    def _wait_until_application_status(self, waiting_status: list[str], target_status: list[str],
                                       error_status: list[str]) -> str:
        start_time = time.time()
        while time.time() - start_time <= self.time_out:
            current_status = self.emr_serverless_gateway.get_emr_serverless_application_state(
                self.connection_details.application_id)
            if current_status in target_status:
                return current_status
            elif current_status in error_status:
                raise RuntimeError(
                    f"Could not start application for {self.connection_name} because application reached terminal status {current_status}")
            elif current_status in waiting_status:
                time.sleep(WAIT_TIME)
            else:
                # ideally this should not be invoked.
                # all the possible status should be covered in waiting_status/target_status/error_status
                raise RuntimeError(
                    f"Application {self.connection_details.application_id} for {self.connection_name} reached illegal status {current_status}")
        raise RuntimeError(
            f"Timed out after {self.time_out} seconds waiting for application to reach {target_status} status.")

    def _install_from_pip(self) -> any:
        # install from pip is not supported in emr serverless
        pass

    def _set_libs(self, properties):
        self.lib_provider.refresh()
        # Add jar
        if self.lib_provider.get_maven_artifacts():
            properties.setdefault("conf", {})
            properties["conf"].setdefault("spark.jars.packages", ",".join(self.lib_provider.get_maven_artifacts()))
        if self.lib_provider.get_other_java_libs() or self.lib_provider.get_s3_java_libs():
            properties.setdefault("conf", {})
            properties["conf"].setdefault("spark.jars", ",".join(self.lib_provider.get_other_java_libs()
                                                                 + self.lib_provider.get_s3_java_libs()))
        if self._openlineage_supported():
            properties.setdefault("conf", {})
            existing_jars = properties["conf"].get("spark.jars", "")
            openlineage_jar = "/usr/share/aws/datazone-openlineage-spark/lib/DataZoneOpenLineageSpark-1.0.jar"
            if existing_jars:
                properties["conf"]["spark.jars"] = f"{existing_jars},{openlineage_jar}"
            else:
                properties["conf"]["spark.jars"] = openlineage_jar

        # Add python
        if self.lib_provider.get_archive():
            # If archive is specified, Skip all other python lib config.
            properties.setdefault("conf", {})
            config = properties["conf"]
            config.setdefault("spark.executorEnv.PYSPARK_PYTHON", "./environment/bin/python")
            config.setdefault("spark.emr-serverless.driverEnv.PYSPARK_DRIVER_PYTHON", "./environment/bin/python")
            config.setdefault("spark.emr-serverless.driverEnv.PYSPARK_PYTHON", "./environment/bin/python")
            config.setdefault("spark.archives", self.lib_provider.get_archive() + "#environment")
        else:
            # https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/using-python-libraries.html
            if self.lib_provider.get_s3_python_libs():
                properties.setdefault("conf", {})
                properties["conf"].setdefault("spark.submit.pyFiles", ",".join(self.lib_provider.get_s3_python_libs()))

    def _lakeformation_session_level_setting_supported(self) -> bool:
        return compare_emr_release_labels(self.release_label, EMR_VERSION_SUPPORT_FOR_LAKEFORMATION) >= 0

    def _openlineage_supported(self) -> bool:
        return compare_emr_release_labels(self.release_label, EMR_VERSION_SUPPORT_FOR_OPENLINEAGE) >= 0

    def _s3ag_supported(self) -> bool:
        return compare_emr_release_labels(self.release_label, EMR_VERSION_SUPPORT_FOR_S3AG) >= 0
