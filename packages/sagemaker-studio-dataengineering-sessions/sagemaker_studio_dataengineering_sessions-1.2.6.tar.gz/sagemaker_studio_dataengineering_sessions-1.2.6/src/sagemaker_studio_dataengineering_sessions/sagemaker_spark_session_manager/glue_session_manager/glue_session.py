import base64
import json
import os
import time
import uuid
from collections import defaultdict

import botocore
from IPython.core.display_functions import publish_display_data
from IPython.core.error import UsageError
from IPython.display import display, HTML, JSON
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.connection_transformer import get_glue_connection

from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_debugging_helper import GlueDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_kernel_utils.GlueSessionsConstants import (
    UNHEALTHY_SESSION_STATUS, NOT_FOUND_SESSION_STATUS, FINAL_STATEMENT_STATUS, TIMEOUT_SESSION_STATUS,
    CANCELLED_STATEMENT_STATUS, WAIT_TIME_IN_SEC, AVAILABLE_STATEMENT_STATUS, COMPLETED_STATEMENT_STATUS,
    ERROR_STATEMENT_STATUS, FAILED_STATEMENT_STATUS, SessionType, READY_SESSION_STATUS, PROVISIONING_SESSION_STATUS,
    MimeTypes, CHINA_REGIONS, US_GOV_REGIONS)
from botocore.exceptions import ClientError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (Language, CONNECTION_TYPE_SPARK_GLUE, USER_ID,
                                                                                                       PROJECT_S3_PATH, DOMAIN_ID, PROJECT_ID,
                                                                                                       IS_REMOTE_WORKFLOW, INPUT_NOTEBOOK_PATH)
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import NoSessionException, StopSessionException, \
    LanguageNotSupportedException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_kernel_utils.KernelGateway import KernelGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_session_configs.config import Config
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_session_configs.glue_conf_utils import \
    dict_to_string, string_to_dict
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_session import SparkSession
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_monitor_widget_utils import \
    add_session_info_in_user_ns, clear_current_connection_in_user_ns
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.common_utils import apply_compatibility_mode_configs
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.metadata_utils import retrieve_sagemaker_metadata_from_file
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.debugging_utils import get_sessions_info_html
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import create_sts_client, create_iam_client, create_s3_client, create_glue_client

# Inherits from SageMakerBaseSessionManager and implements all of its abstract methods.
class GlueSession(SparkSession):
    # Taking the default value from glue
    # https://code.amazon.com/packages/AWSGlueInteractiveSessionsKernel/blobs/2a2be9534b64d6eba3366eec65d0011ca2acfa5d/--/src/aws_glue_interactive_sessions_kernel/glue_kernel_base/BaseKernel.py#L46
    # The number of minutes before session times out.
    time_out = float("inf")

    def __init__(self, connection_name: str, language=Language.python):
        # The connection_details are required to get the profile, which is needed for super.__init__
        self.connection_details = get_glue_connection(connection_name, self.get_logger())
        super().__init__(connection_name)
        self.session_type = None
        self.iam_client = create_iam_client(self.profile, self.region)
        self.s3_client = create_s3_client(self.profile, self.region)
        self.kernel_gateway = KernelGateway(self.glue_client,
                                            self.sts_client,
                                            self.iam_client, 
                                            self.s3_client)
        self.connection_type = CONNECTION_TYPE_SPARK_GLUE
        self.language = language
        self.additional_arguments = {}
        self.max_capacity = None
        self.worker_type = None
        self.number_of_workers = None
        self.connections = []
        self.connections_override = []
        self.custom_spark_configuration = {}
        self.default_glue_spark_configuration = {}
        self.debugging_helper = GlueDebuggingHelper(self.glue_gateway, self)


        self._reset_session()

        if self._openlineage_supported():
            self.default_glue_spark_configuration = {
                "spark.extraListeners": "io.openlineage.spark.agent.OpenLineageSparkListener",
                "spark.openlineage.transport.type": "amazon_datazone_api",
                "spark.openlineage.transport.domainId": DOMAIN_ID,
                "spark.openlineage.facets.custom_environment_variables":
                "[AWS_DEFAULT_REGION;GLUE_VERSION;GLUE_COMMAND_CRITERIA;GLUE_PYTHON_VERSION;]",
                "spark.glue.accountId": self.connection_details.account,
            }
        if IS_REMOTE_WORKFLOW and INPUT_NOTEBOOK_PATH:
            self.default_glue_spark_configuration["spark.glue.JOB_NAME"] = f"{PROJECT_ID}.{INPUT_NOTEBOOK_PATH}"
        elif not IS_REMOTE_WORKFLOW:
            try:
                username = self.datazone_gateway.get_username(USER_ID)
            except Exception as e:
                self.logger.error(f"Failed to get username from DataZone: {e}")
                username = "unknown_user"
            self.default_glue_spark_configuration["spark.glue.JOB_NAME"] = f"Interactive/{PROJECT_ID}/{username}"
        if self._s3ag_supported():
            try:
                env = self.datazone_gateway.get_project_tooling_environment(project_id=PROJECT_ID)
                if self.datazone_gateway.is_s3_ag_enabled_for_environment(env):
                    self.default_glue_spark_configuration.update({
                        "spark.hadoop.fs.s3.s3AccessGrants.enabled": "true",
                        "spark.hadoop.fs.s3.s3AccessGrants.fallbackToIAM": "true"
                    })
                    self.logger.info("S3 Access Grants enabled for Spark configuration")
            except Exception as e:
                self.logger.warning(f"Failed to check S3 AG status: {e}")

        if self._is_fta_supported():
            # Apply spark compatibility configs if compatibility mode is enabled for glue session
            self.logger.info(f"Applying compatibility mode configs for Glue connection {self.connection_name}")
            self.default_glue_spark_configuration = apply_compatibility_mode_configs(self.default_glue_spark_configuration)
        
    def create_session_operate(self):
        self.get_logger().info(f"Creating a Glue session.")
        SageMakerConnectionDisplay.write_msg("Creating Glue session...")

        additional_args = self._get_additional_arguments()

        number_of_workers = additional_args.get("NumberOfWorkers")
        worker_type = additional_args.get("WorkerType")
        max_capacity = additional_args.get("MaxCapacity")

        # https://docs.aws.amazon.com/glue/latest/webapi/API_Session.html#Glue-Type-Session-MaxCapacity
        # max_capacity is of Double and number_of_workers is of Integer
        if not (number_of_workers and worker_type):
            if not max_capacity:
                raise ValueError(
                    f"Either max_capacity or worker_type and number_of_workers must be set, all are none."
                )
            self.max_capacity = max_capacity
        else:
            if max_capacity:
                setattr(self.configs, "max_capacity", None)
                del self.additional_arguments["MaxCapacity"]
                raise ValueError(f"Either max_capacity or worker_type and number_of_workers must be set, but not both.")
            self.number_of_workers = number_of_workers
            self.worker_type = worker_type

        if self.configs.session_type:
            # session type has been overridden by magic
            session_type = self.configs.session_type
        else:
            # session type should be configured in connection file; etl will be provided by default
            session_type = self.connection_details.session_configs.get("session_type", "etl")
        self.session_type = session_type
        session_type_enum = SessionType[session_type]

        if self.configs.session_id_prefix:
            # session_id_prefix has been configured by magic
            new_session_id = f"{self.configs.session_id_prefix}-{self.connection_details.project}-{uuid.uuid4()}"
        else:
            new_session_id = f"{self.connection_details.project}-{uuid.uuid4()}"

        glue_role_arn = self.connection_details.glue_iam_role

        session_default_arguments = self._get_default_arguments()
        SageMakerConnectionDisplay.write_critical_msg(self.CREATE_SESSION_MSG.format(self.connection_name))
        response = self.kernel_gateway.create_session(role=glue_role_arn,
                                                      default_arguments=session_default_arguments,
                                                      new_session_id=new_session_id,
                                                      command={"Name": session_type_enum.session_type(),
                                                               "PythonVersion": session_type_enum.python_version()},
                                                      **additional_args)

        self.session_id = response["Session"]["Id"]
        self.get_logger().info(f"Session created with {self.session_id}")
        start_time = time.time()
        while time.time() - start_time <= self.time_out:
            current_status = self._get_session_status()
            if current_status == READY_SESSION_STATUS:
                self.session_started = True
                # Send datazone metadata when the session is ready.
                self.send_datazone_metadata_to_remote(self.language)
                self.get_logger().info(f"Session {self.session_id} ready")
                SageMakerConnectionDisplay.display(f"Session {self.session_id} has been created.")
                self._display_debugging_links(self.session_id, session_default_arguments)
                return

            elif current_status == PROVISIONING_SESSION_STATUS:
                time.sleep(WAIT_TIME_IN_SEC)
                continue
            elif current_status in UNHEALTHY_SESSION_STATUS:
                self.session_started = False
                self.get_logger().error(
                    f"Session {self.session_id} reached terminal state {self._get_session_status()}")
                SageMakerConnectionDisplay.send_error(f"Session {self.session_id} reached terminal state "
                                                    f"{self._get_session_status()}")
                raise RuntimeError(
                    f"Session failed to reach {READY_SESSION_STATUS} "
                    f"instead reaching terminal state {self._get_session_status()}.")
            else:
                time.sleep(WAIT_TIME_IN_SEC)
                continue

        if time.time() - start_time > self.time_out:
            self.session_started = False
            self.get_logger().error(f"Session {self.session_id} did not start within {self.time_out}")
            SageMakerConnectionDisplay.send_error(f"Timed out after {self.time_out} seconds waiting for session "
                                                f"to reach {READY_SESSION_STATUS} status.")
            raise RuntimeError(
                f"Timed out after {self.time_out} seconds waiting for session to reach {READY_SESSION_STATUS} status.")

    def run_statement(self, cell="", language=Language.python, interactive_debugging=True, **kwargs):
        clear_current_connection_in_user_ns()
        add_session_info_in_user_ns(connection_name=self.connection_name, connection_type=CONNECTION_TYPE_SPARK_GLUE,
                                    session_id=self.session_id)
        self.get_logger().info(f"Running statement")
        if not language.supports_connection_type(CONNECTION_TYPE_SPARK_GLUE):
            raise LanguageNotSupportedException(f"Language {language.name} not supported for Spark Glue")
        if not self.session_started:
            raise NoSessionException(f"Session not exist for {self.connection_name}")
        # Creating a session with Scala will cause all cells in the session to run using Scala
        if self.language == Language.scala and language == Language.python:
            raise LanguageNotSupportedException(f"Glue session already started in {self.language.name}. "
                                                f"Please select language {Language.scala.name} or {Language.sql.name}.")
        # Creating a session with either SQL or PySpark will cause all cells in the session to run using Python
        elif self.language != Language.scala and language == Language.scala:
            raise LanguageNotSupportedException(f"Glue session already started in {self.language.name}. "
                                                f"Please select language {Language.python.name} or {Language.sql.name}.")
        # This SparkSQL syntax works in both Scala and PySpark, so the session's language does not impact SQL cells
        if language == Language.sql:
            cell = f'spark.sql("""{cell.rstrip()}""").show()'
        statement_id = None
        try:
            statement_id = self.kernel_gateway.run_statement(session_id=self.session_id, code=cell)["Id"]
            start_time = time.time()
            self.get_logger().info(f"Statement {statement_id} submitted.")
            try:
                while time.time() - start_time <= self.time_out:
                    statement = self.kernel_gateway.get_statement(self.session_id, statement_id)["Statement"]
                    if statement["State"] in FINAL_STATEMENT_STATUS:
                        return self._reply_to_statement(statement, interactive_debugging)
                    time.sleep(WAIT_TIME_IN_SEC)  # WAIT_TIME_IN_SECONDS
                self.get_logger().error(f"Timeout occurred with statement (statement_id={statement_id}")
                raise RuntimeError(f"Timeout occurred with statement (statement_id={statement_id}")
            except KeyboardInterrupt:
                self.get_logger().warning(
                    f"Execution Interrupted. Attempting to cancel the statement (statement_id={statement_id})")
                self.kernel_gateway.cancel_statement(self.session_id, statement_id)
        except ClientError as e:
            self.get_logger().error(f"Client error when running statement {statement_id}. Error: {e}")
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code in "InvalidInputException":
                if self._get_session_status() == TIMEOUT_SESSION_STATUS:
                    self.get_logger().info(f"stopping session: {self.session_id}")
                    self.stop_session()
                    raise RuntimeError(
                        f"session_id={self.session_id} has reached {self._get_session_status()} status. "
                        f"Please re-run the same cell to restart the session. You may also need to re-run "
                        f"previous cells if trying to use pre-defined variables."
                    )
            else:
                self._cancel_statement(statement_id)
                raise RuntimeError(error_message)

    def stop_session(self):
        try:
            SageMakerConnectionDisplay.writeln(
                f"Stopping session for {self.connection_name}. Session id: {self.session_id}")
            self.get_logger().info(f"Stopping session: {self.session_id}")
            self.kernel_gateway.stop_session(self.session_id)
            self._reset_session()
            SageMakerConnectionDisplay.writeln(f"Session stopped.")
        finally:
            self.post_session_stopped()

    def post_session_stopped(self):
        if self.debugging_helper is not None:
            self.debugging_helper.clean_up()

    def is_session_connectable(self) -> bool:
        if not self.session_started:
            return False

        current_status = self._get_session_status()
        if current_status in UNHEALTHY_SESSION_STATUS:
            return False

        return True

    def add_tags(self, tags):
        valid_tags = self._validate_dict(json.loads(tags))
        if self._get_session_status() == READY_SESSION_STATUS:
            session_id = self.session_id
            resource_arn = self._create_resource_arn()
            if not valid_tags:
                return

            try:
                self.kernel_gateway.tag_resource(resource_arn, valid_tags)
                SageMakerConnectionDisplay.display(f"The following configurations have been updated: {valid_tags}")
                return
            except botocore.exceptions.ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "AccessDeniedException":
                    SageMakerConnectionDisplay.display(
                        "Tags: Unable to display tags due to missing glue:GetTags permission. "
                        "Please update your IAM policy.")
                    return
                else:
                    SageMakerConnectionDisplay.display(f"Unable to add tags for the session: {session_id} "
                                                     f"due to error {error_code}")
                    return

        converted = {
            "tags": valid_tags
        }
        # converting json obj to str
        converted_str = json.dumps(converted, indent=0)
        self.configure(converted_str)
        return

    def get_session_id(self):
        if self.session_id:
            if self.is_session_connectable():
                SageMakerConnectionDisplay.display(f"Current active Session ID: {self.session_id}")
            else:
                SageMakerConnectionDisplay.display(f"Current session is not connectable "
                                                 f"either because it's not started yet, "
                                                 f"or is in an unhealthy session status. "
                                                 f"Session ID: {self.session_id}")
        else:
            SageMakerConnectionDisplay.display("There is no current session.")

    def get_status(self):
        if not self.session_id:
            SageMakerConnectionDisplay.display(f"There is no current session.")
            return

        session = self._get_current_session()
        status = self._get_session_status()
        role = self._get_current_session_role()
        
        if session["Command"]:
            session_type = session["Command"]["Name"]
        else:
            session_type = self.session_type
        result = {
            "Session ID": session["Id"],
            "Status": status,
            "Role": role,
            "CreatedOn": session["CreatedOn"],
            "GlueVersion": session["GlueVersion"],
            "SessionType": session_type,
            "IdleTimeout": session['IdleTimeout'],
            "MaxCapacity": self.max_capacity,
            "Region": self.connection_details.region,
            "Connections": self._get_session_connections(),
            "SessionsArgs": self.default_arguments
        }
        if self.max_capacity:
            result.update({"MaxCapacity": self.max_capacity})
        else:
            result.update({
                "WorkerType": self.worker_type,
                "NumWorkers": self.number_of_workers
            })
        tags, exception_error = self._get_tags_from_resource()

        if exception_error:
            SageMakerConnectionDisplay.display(exception_error)
        else:
            result.update({"Tags": tags})

        SageMakerConnectionDisplay.display(JSON(result, expanded=True))
        SageMakerConnectionDisplay.write_critical_msg(self.INFO_TABLE_MSG.format(self.connection_name))
        self._display_debugging_links(session["Id"], self.default_arguments)
        return result

    # %info magic is alias for %status magic in Glue
    def get_info(self):
        self.get_status()

    def set_session_id_prefix(self, prefix, force=False):
        session_id_prefix = f'{{"session_id_prefix": "{prefix}"}}'
        self.configure(session_id_prefix, force)

    def set_number_of_workers(self, number, force=False):
        number_of_workers = f'{{"number_of_workers": "{number}"}}'
        self.configure(number_of_workers, force)

    def set_worker_type(self, type, force=False):
        worker_type = f'{{"worker_type": "{type}"}}'
        self.configure(worker_type, force)

    def set_session_type(self, session_type, force=False):
        session_type = f'{{"session_type": "{session_type}"}}'
        self.configure(session_type, force)

    def set_glue_version(self, glue_version, force=False):
        glue_version = f'{{"glue_version": "{glue_version}"}}'
        self.configure(glue_version, force)

    def set_idle_timeout(self, idle_timeout, force=False):
        idle_timeout = f'{{"idle_timeout": "{idle_timeout}"}}'
        self.configure(idle_timeout, force)

    def spark_conf(self, spark_conf, force=False):
        spark_conf = f'{{"spark_conf": "{spark_conf}"}}'
        self.configure(spark_conf, force)

    def _reset_session(self):
        self.session_started = False
        self.session_id = None
        self.configs = Config()
        self.default_arguments = self._create_default_arguments()

    def _configure_core(self, cell):
        try:
            configurations = json.loads(cell)
        except ValueError:
            SageMakerConnectionDisplay.send_error(f"Could not parse JSON object from input '{format(cell)}'")
            self.get_logger().error(f"Could not parse JSON object from input '{format(cell)}'")
            return

        if not configurations:
            SageMakerConnectionDisplay.send_error("No configuration values were provided.")
            self.get_logger().error("No configuration values were provided.")
            return

        for arg, val in configurations.items():
            if arg == "--conf":
                # manage spark conf in dict instead of string
                if not isinstance(val, str):
                    raise UsageError("Invalid input for '--conf': Please provide a simple text string. Example: 'key1=value1 --conf key2=value2'")
                self.custom_spark_configuration.update(string_to_dict(val))
            elif arg == "spark_conf":
                # manage spark conf in dict instead of string
                if not isinstance(val, str):
                    raise UsageError("Invalid input for 'spark_conf': Please provide a simple text string. Example: 'key1=value1 --conf key2=value2'")
                self.custom_spark_configuration.update(string_to_dict(val))
            elif arg == "conf":
                if not isinstance(val, dict):
                    raise UsageError("Invalid input for 'conf': Please provide a dictionary of key-value pairs. Example: {'key1': 'value1', 'key2': 'value2'}")
                self.custom_spark_configuration.update(val)
            elif arg == "endpoint_url":
                local_glue_client = create_glue_client(self.profile, self.region, val)
                self.kernel_gateway = KernelGateway(local_glue_client, self.sts_client, self.iam_client, self.s3_client)
            elif arg == "connections":
                self.connections = [connection.strip() for connection in val.split(",")]
            elif arg == "connections_override":
                self.connections_override = [connection.strip() for connection in val.split(",")]
            elif arg == "auto_add_catalogs":
                self._set_auto_add_catalogs(val)
            elif arg not in Config().__dict__:
                # These will be the parameter such as "--enable-glue-datacatalog": "false"
                self._add_default_argument(arg, val)
            elif arg == "tags":
                tags_to_add = configurations.get("tags")
                if isinstance(tags_to_add, str):
                    # This branch is for %%tags directly as the input will be str so convert it back to a json obj
                    self._add_tag(json.loads(tags_to_add))
                else:
                    self._add_tag(tags_to_add)
            else:
                setattr(self.configs, arg, val)

        SageMakerConnectionDisplay.display(f"The following configurations have been updated: {configurations}")

    def _validate_dict(self, dictionary):
        if not dictionary:
            return None
        else:
            return dict((key.strip(), value.strip()) for key, value in dictionary.items())

    def _add_tag(self, tags_to_add):
        tags = getattr(self.configs, "tags", defaultdict())
        for (key, value) in tags_to_add.items():
            tags[key] = value

    def _get_tags_from_resource(self):
        session_id = self.session_id
        resource_arn = self._create_resource_arn()
        try:
            return self.kernel_gateway.get_tags(resource_arn), None
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDeniedException":
                return None, ("Tags: Unable to display tags due to missing glue:GetTags permission. "
                              "Please update your IAM policy.")
            else:
                return None, f"Unable to fetch tags for the session: {session_id} due to error {error_code}"

    def _create_resource_arn(self):
        region = self.connection_details.region
        account = self.connection_details.account
        session_id = self.session_id

        if region in CHINA_REGIONS:
            resource_arn = "arn:aws-cn:glue:" + region + ":" + account + ":session/" + session_id
        elif region in US_GOV_REGIONS:
            resource_arn = "arn:aws-us-gov:glue:" + region + ":" + account + ":session/" + session_id
        else:
            resource_arn = "arn:aws:glue:" + region + ":" + account + ":session/" + session_id
        return resource_arn

    def _get_current_session(self):
        if not self.session_id:
            SageMakerConnectionDisplay.display(f"There is no current session.")
            return

        return self.kernel_gateway.get_session(self.session_id)["Session"]

    def _get_current_session_role(self):
        try:
            return self._get_current_session()["Role"]
        except Exception as e:
            SageMakerConnectionDisplay.send_error("Failed to retrieve current session role.")

    def _get_session_connections(self):
        try:
            return self._get_current_session()["Connections"]
        except Exception as e:
            SageMakerConnectionDisplay.send_error("Failed to retrieve current session connections.")

    def _get_session_status(self) -> str:
        session_id = self.session_id
        if session_id is None:
            return NOT_FOUND_SESSION_STATUS

        session = self._get_current_session()
        if session is None:
            return NOT_FOUND_SESSION_STATUS

        return session["Status"]

    # This is temporary to support private beta use case:
    # Access redshift via glue
    # same as:
    # https://code.amazon.com/packages/AWSGlueInteractiveSessionsKernel/commits/0e42fe7fbde5fdd559bb7c2635c10daf4b09af50
    # This need to change once the approach of using Redshift connection from a Glue connection is finalized
    def _add_redshift_default_arguments(self, default_arguments):
        try:
            if self.connection_details.related_redshift_properties:
                default_arguments["--redshift_url"] = self.connection_details.related_redshift_properties["jdbcUrl"]
                default_arguments["--redshift_tempdir"] = self.connection_details.related_redshift_properties["redshiftTempDir"]
                default_arguments["--redshift_iam_role"] = self.connection_details.related_redshift_properties["iamRole"]
                default_arguments["--redshift_jdbc_iam_url"] = self.connection_details.related_redshift_properties["jdbcIamUrl"]
                default_arguments["--datazone_domain_id"] = DOMAIN_ID
                default_arguments["--redshift_datazone_connection_id"] = self.connection_details.related_redshift_properties[
                    "connectionId"]
        except Exception as e:
            SageMakerConnectionDisplay.writeln("Cannot add additional default arguments for Redshift.")
            self.get_logger().error(f"Unable to add redshift default arguments: {e}")
            return

    def _get_default_arguments(self) -> dict:
        self._add_redshift_default_arguments(self.default_arguments)
        # Using update method as self.default_arguments have value populated already
        connection_list = []
        connection_list.extend(self._get_glue_connection_names())
        if connection_list:
            self.default_arguments.update({"--connection-names": ",".join(connection_list)})

        if self.language == Language.scala:
            self.default_arguments["--session-language"] = "scala"

        # TODO: leverage spark_configs in glue connections
        # spark configuration are from 4 different sources
        # 1. Connection defined configuration. Stored in default_spark_configuration. Defined in connection detail.
        # 2. Auto added configuration for GlueCatalog. Stored in default_spark_configuration. Only auto added if iceberg is enabled
        # 3. Auto added configuration for Glue. Stored in default_glue_spark_configuration. The configurations are initialized during session creation and remain constant throughout the session.
        # 4. Customer defined configurations. Stored in custom_spark_configuration. From configure magic fields conf, --conf or spark_conf
        spark_conf = {}
        if ("--datalake-formats" in self.default_arguments.keys()
                and self.default_arguments["--datalake-formats"] == "iceberg"):
            self._set_iceberg_enabled(True)
        else:
            self._set_iceberg_enabled(False)
        spark_conf.update(self.default_spark_configuration)
        spark_conf.update(self.default_glue_spark_configuration)
        spark_conf.update(self.custom_spark_configuration)
        self.default_arguments["--conf"] = dict_to_string(spark_conf)

        self._add_libs_default_arguments(self.default_arguments)

        return self.default_arguments

    def _add_default_argument(self, arg, val):
        arg = str(arg) if str(arg).startswith("--") else f'--{arg}'
        val = str(val)

        self.default_arguments[arg] = val

    def _get_additional_arguments(self) -> dict:
        connection_list = []
        if self.connection_details.glue_connection:
            connection_list.append(self.connection_details.glue_connection)
        connection_list.extend(self._get_glue_connection_names())
        self.additional_arguments["Connections"] = {"Connections": connection_list}

        tags = self.configs.tags
        if self.connection_details.project is not None:
            tags["AmazonDataZoneProject"] = self.connection_details.project
        try:
            source_identity = self.sts_gateway.get_source_identity()
            if source_identity is not None:
                tags["AmazonDataZoneSessionOwner"] = source_identity
        except Exception:
            SageMakerConnectionDisplay.send_error("Failed to retrieve source identity.")

        self.additional_arguments["Tags"] = tags

        metadata = retrieve_sagemaker_metadata_from_file(self.get_logger())
        # If the resource-metadata.json file exists on the SageMaker space under /opt/ml/metadata directory,
        # then it's an interactive notebook; otherwise, it's a headless notebook.
        if metadata:
            self.additional_arguments["RequestOrigin"] = "SageMakerUnifiedStudio_NotebookRun"
        else:
            self.additional_arguments["RequestOrigin"] = "SageMakerUnifiedStudio_NotebookScheduledRun"

        # Always apply values from connection.session_configs
        if self.connection_details.session_configs is not None:
            self.additional_arguments["GlueVersion"] = self.connection_details.session_configs["glue_version"]
            self.additional_arguments["IdleTimeout"] = int(self.connection_details.session_configs["idle_timeout"])
            self.additional_arguments["NumberOfWorkers"] = int(self.connection_details.session_configs["number_of_workers"])
            self.additional_arguments["WorkerType"] = self.connection_details.session_configs["worker_type"]

        # Override values if configs have been populated by magics
        if self.configs.glue_version:
            self.additional_arguments["GlueVersion"] = self.configs.glue_version
        if self.configs.idle_timeout:
            self.additional_arguments["IdleTimeout"] = int(self.configs.idle_timeout)
        if self.configs.number_of_workers:
            self.additional_arguments["NumberOfWorkers"] = int(self.configs.number_of_workers)
        if self.configs.worker_type:
            self.additional_arguments["WorkerType"] = self.configs.worker_type
        if self.configs.max_capacity:
            self.additional_arguments["MaxCapacity"] = float(self.configs.max_capacity)
        if self.configs.security_config:
            self.additional_arguments["SecurityConfiguration"] = self.configs.security_config
        if self.configs.timeout:
            self.additional_arguments["Timeout"] = int(self.configs.timeout)
            self.time_out = int(self.configs.timeout)

        return self.additional_arguments

    def _reply_to_statement(self, statement, interactive_debugging=True):
        statement_output = statement["Output"]
        status = statement["State"]
        reply = None

        if status in (AVAILABLE_STATEMENT_STATUS, COMPLETED_STATEMENT_STATUS):
            if status == COMPLETED_STATEMENT_STATUS or (
                    "Status" in statement_output and statement_output["Status"] == "ok"
            ):
                return self._display_result(statement_output)
            else:
                reply = f'{statement_output["ErrorName"]}:{statement_output["ErrorValue"]}'
        elif status == ERROR_STATEMENT_STATUS:
            reply = str(statement_output)
        elif status == FAILED_STATEMENT_STATUS:
            if "Data" in statement_output:
                statement_output_data = statement_output["Data"]
                stdout_text = self.kernel_gateway.get_results(
                    statement_output_data["StdOut"]) if "StdOut" in statement_output_data else ""
                if len(stdout_text):
                    reply = stdout_text
                failure_reason = self.kernel_gateway.get_results(
                    statement_output_data["Result"]) if "Result" in statement_output_data else ""
                if len(failure_reason):
                    reply = failure_reason
                stderr_text = self.kernel_gateway.get_results(
                    statement_output_data["StdErr"]) if "StdErr" in statement_output_data else ""
                if len(stderr_text):
                    reply = stderr_text
        elif status == CANCELLED_STATEMENT_STATUS:
            reply = "This statement is cancelled"

        self.handle_spark_error(error_message=reply, interactive_debugging=interactive_debugging)

    def _cancel_statement(self, statement_id: str):
        if not statement_id:
            return

        try:
            self.get_logger().info(f"Cancelling statement: {statement_id}")
            self.kernel_gateway.cancel_statement(self.session_id, statement_id)
            start_time = time.time()
            is_ready = False

            while time.time() - start_time <= self.time_out and not is_ready:
                status = self.kernel_gateway.get_statement(self.session_id, statement_id)["Statement"]["State"]
                if status == CANCELLED_STATEMENT_STATUS:
                    self.get_logger().info(f"Statement {statement_id} has been cancelled.")
                    is_ready = True

                time.sleep(WAIT_TIME_IN_SEC)  # WAIT_TIME_IN_SECONDS

            if is_ready:
                raise RuntimeError(
                    f"Failed to cancel the statement {statement_id} as it has been cancelled"
                )
            else:
                raise RuntimeError(
                    f"Timeout occurred when cancelling statement (statement_id={statement_id}"
                )
        except Exception as e:
            self.get_logger().error(f"Exception encountered when cancelling statement {statement_id}: {e}")
            raise RuntimeError(
                f"Exception encountered while canceling statement {statement_id}: {e} \n"
            )

    def _display_debugging_links(self, session_id, session_argument):
        events_logs_location = session_argument.get("--spark-event-logs-path", "")
        system_logs_location = session_argument.get("--spark-logs-s3-uri", "")
        driver_logs_location = f"{system_logs_location}{session_id}/driver/stderr.gz"
        html = get_sessions_info_html(self.session_id, events_logs_location, driver_logs_location)
        display(HTML(html))

    # If result is plain text response, return the result rather than displaying it,
    # if image or other type display with existing glue-specific functionality and return None
    def _display_result(self, statement_output):
        # a basic example output for 1+1
        # {'Data': {'TextPlain': '2'}, 'Status': 'ok'}
        if "Data" in statement_output:
            statement_output_data = statement_output["Data"]
            # The default case would be a text/plain response,
            # but an image result may also be accompanied by a text output.
            if MimeTypes.TextPlain.name in statement_output_data and len(statement_output_data) == 1:
                # The value for dictionary key in the result is: text/plain
                out = statement_output_data[MimeTypes.TextPlain.name].strip("'")
                if out.startswith("[") and out.endswith("]"):  # PARSE TO DICT
                    list_out = out.replace("'", '"')
                    try:
                        return json.loads(list_out)
                    except:
                        return out
                try:
                    return int(out)
                except ValueError:
                    pass
                try:
                    return float(out)
                except ValueError:
                    pass
                return out
            elif "MimeType" in statement_output_data:
                result = statement_output_data["Result"]
                mime_type = statement_output_data["MimeType"]

                # Unpack the inline vs. indirect std streams
                if mime_type == MimeTypes.S3URI.value:
                    stdout_text = self.kernel_gateway.get_results(statement_output_data["StdOut"]) \
                        if "StdOut" in statement_output_data else ""
                    stderr_text = self.kernel_gateway.get_results(statement_output_data["StdErr"]) \
                        if "StdErr" in statement_output_data else ""
                else:
                    stdout_text = statement_output_data["StdOut"] if "StdOut" in statement_output_data else ""
                    stderr_text = statement_output_data["StdErr"] if "StdErr" in statement_output_data else ""

                if mime_type == MimeTypes.S3URI.value:
                    response = self.kernel_gateway.get_results(statement_output_data["Result"])
                    result = json.loads(response)
                    if len(result) == 0:
                        # Semantically this case corresponds to the 'stream' result,
                        # which is meant to be "send_output'd" and actually
                        # arriving at stdout which is headed there anyway.
                        result = None
                        mime_type = None
                    elif result.get(MimeTypes.ImagePng.value):
                        result = result.get(MimeTypes.ImagePng.value)
                        mime_type = MimeTypes.ImagePng.value
                    elif result.get(MimeTypes.TextPlain.value):
                        result = result.get(MimeTypes.TextPlain.value)
                        mime_type = MimeTypes.TextPlain.value

                if mime_type and ";" in mime_type:
                    mime_type_list = mime_type.replace(' ', '').split(';')
                    if "base64" in mime_type_list:
                        result = base64.b64decode(str(result))
                        mime_type_list.remove("base64")
                        mime_type = ";".join(mime_type_list)

                # Dispatch of results for display
                if stdout_text:
                    SageMakerConnectionDisplay.writeln(stdout_text)
                    return
                if stderr_text:
                    SageMakerConnectionDisplay.writeln(stderr_text)
                    return
                if result and mime_type:
                    display_data = {
                        mime_type: result
                    }
                    publish_display_data(data=display_data, metadata={mime_type: {"width": 640, "height": 480}})

    def _add_libs_default_arguments(self, default_arguments):
        self.lib_provider.refresh()
        # Add jar
        if self.lib_provider.get_s3_java_libs():
            default_arguments.setdefault("--extra-jars", ",".join(self.lib_provider.get_s3_java_libs()))

        # Add python
        if self.lib_provider.get_s3_python_libs() or self.lib_provider.get_other_python_libs():
            default_arguments.setdefault("--extra-py-files",
                                         ",".join(self.lib_provider.get_s3_python_libs()
                                                  + self.lib_provider.get_other_python_libs()))
        if self.lib_provider.get_pypi_modules():
            default_arguments.setdefault("--additional-python-modules",
                                         ",".join(self.lib_provider.get_pypi_modules()))

    def _get_glue_connection_names(self):
        if self.connections_override:
            # if customer provide `connections_override`, use connections_override
            return self.connections_override
        else:
            # else using all ready glue connections and customer provided connections in `connections`
            connection_list = []
            connection_list.extend(SageMakerToolkitUtils.get_glue_connection_names())
            connection_list.extend(self.connections)
            return connection_list

    def _create_default_arguments(self):
        default_arguments = {
            "--enable-spark-live-ui": "true",
            "--enable-spark-ui": "true",
            "--enable-glue-datacatalog": "true",
            "--enable-auto-scaling": "true",
            "--datalake-formats" : "iceberg"
        }

        if PROJECT_S3_PATH:
            spark_event_logs_path = f"{PROJECT_S3_PATH}/glue/glue-spark-events-logs/"
            spark_system_logs_path = f"{PROJECT_S3_PATH}/glue/glue-spark-system-logs/"
            default_arguments.update({
                "--spark-event-logs-path": spark_event_logs_path,
                "--spark-logs-s3-uri": spark_system_logs_path
            })
        else:
            self.get_logger().warning(f"Session for {self.connection_details.connection_id} will not have "
                                      f"--spark-event-logs-path and --spark-logs-s3-uri, "
                                      f"because project s3 path does not exist")
        default_arguments.update(self.connection_details.default_arguments)
        return default_arguments

    def _lakeformation_session_level_setting_supported(self) -> bool:
        return True

    def _openlineage_supported(self) -> bool:
        try:
            version = float(self.connection_details.session_configs.get("glue_version", "0"))
            return version >= 5.0
        except (ValueError, TypeError):
            return False

    def _s3ag_supported(self) -> bool:
        try:
            version = float(self.connection_details.session_configs.get("glue_version", "0"))
            return version >= 5.0
        except (ValueError, TypeError):
            return False
        
    def _is_fta_supported(self):
        try:
            version = float(self.connection_details.session_configs.get("glue_version", "0"))
            return version >= 5.0 and self.connection_details.session_configs.get("is_compatibility_mode", False)
        except (ValueError, TypeError):
            return False
