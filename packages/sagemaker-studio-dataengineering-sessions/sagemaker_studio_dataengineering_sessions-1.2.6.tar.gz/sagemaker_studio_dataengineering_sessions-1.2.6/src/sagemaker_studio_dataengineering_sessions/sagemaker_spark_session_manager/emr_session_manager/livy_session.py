from IPython.display import JSON
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import Language
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import NoSessionException, \
    LanguageNotSupportedException, ExecutionException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_connection import EmrOnEc2Connection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_connection import \
    EmrOnServerlessConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.spark_magic import SparkMagic
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_session import SparkSession
from sparkmagic.livyclientlib.endpoint import Endpoint
from sparkmagic.utils.constants import FINAL_STATUS, MIMETYPE_TEXT_HTML

from sparkmagic.utils.utils import get_sessions_info_html
from sparkmagic.livyclientlib.command import Command
import sparkmagic.utils.configuration as conf
import json
from six import string_types

LANGUAGE_LIVY_KIND_MAP = {
    Language.python: "pyspark",
    Language.scala: "spark",
}

AUTHENTICATOR = {
    "Kerberos": "sparkmagic.auth.kerberos.Kerberos",
    "None": "sparkmagic.auth.customauth.Authenticator",
    "Basic_Access": "sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.custom_authenticator.EMRonEc2CustomAuthenticator",
    # change to default emr_serverless auth when it supports profile
    # "Custom_Auth": "emr_serverless_customauth.customauthenticator.EMRServerlessCustomSigV4Signer"
    "Custom_Auth": "sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.custom_authenticator.EMRServerlessCustomSigV4Signer"
}

# Do not change this string template without updating the SageMakerDebuggingJLPlugin
CONNECTION_INFO_EMR_EC2_TEMPLATE = "Compute details - Cluster Id: {}, Runtime role: {}\n"
# Do not change this string template without updating the SageMakerDebuggingJLPlugin
CONNECTION_INFO_EMR_SERVERLESS_TEMPLATE = "Compute details - Application Id: {}\n"

class LivySession(SparkSession):
    def __init__(self, connection_name: str):
        super().__init__(connection_name)
        self.spark_magic = SparkMagic()
        self.language = "python"
        self.endpoint = None
        self.session_started = False
        self.config_dict = {}

    def create_livy_endpoint(self) -> Endpoint:
        raise NotImplementedError("create_livy_endpoint is not implemented yet")

    def configure_properties(self) -> any:
        raise NotImplementedError("configure_properties is not implemented yet")

    def pre_run_statement(self):
        pass

    def prepare_spark_configuration(self):
        super().prepare_spark_configuration()

        default_livy_conf = {
            "conf": self.default_spark_configuration
        }
        conf.override(conf.session_configs_defaults.__name__, default_livy_conf)

    def post_session_stopped(self):
        if self.debugging_helper is not None:
            self.debugging_helper.clean_up()

    def handle_exception(self, e: Exception):
        self.get_logger().error(f"Error encountered while handling livy session {e.__class__.__name__}: {e}")
        raise e

    def create_session_operate(self):
        endpoint = self.create_livy_endpoint()
        self.prepare_spark_configuration()
        properties = self.configure_properties()
        self._set_libs(properties)
        try:
            self.get_logger().info("Starting EMR Livy session.")
            # if a session already exists in sparkmagic spark controller
            # it should mean that the session errored out, but did not get cleaned up
            # we will clean up before starting
            if self.connection_name in self.spark_magic.spark_controller.session_manager.get_sessions_list():
                self.spark_magic.spark_controller.session_manager._sessions.pop(self.connection_name)
                self.session_started = False
                self.endpoint = None
            SageMakerConnectionDisplay.write_critical_msg(self.CREATE_SESSION_MSG.format(self.connection_name))
            self.spark_magic.spark_controller.add_session(self.connection_name, endpoint, False, properties)
            self.session_started = True
            self.endpoint = endpoint
            SageMakerConnectionDisplay.write_critical_msg(self._get_connection_info())
            self.send_datazone_metadata_to_remote()
            self._install_from_pip()
        except Exception as e:
            self.session_started = False
            self.endpoint = None
            self.handle_exception(e)

    def get_app_id(self):
        return self.spark_magic.spark_controller.get_app_id(self.connection_name)

    def matplot(self, line):
        session = self.spark_magic.spark_controller.get_session_by_name_or_default(
            self.connection_name
        )

        command = Command("%matplot " + line)

        (success, out, mimetype) = command.execute(session)
        if success:
            SageMakerConnectionDisplay.display(out)
        else:
            SageMakerConnectionDisplay.send_error(out)

    def run_statement(self, cell="", language=Language.python, interactive_debugging=True, **kwargs):
        self.pre_run_statement()
        self.get_logger().info(f"Running statement for {language}")
        if not language.supports_connection_type(SageMakerToolkitUtils.get_connection_type(self.connection_name)):
            self.get_logger().error(f"Language {language.name} not supported for Spark EMR")
            raise LanguageNotSupportedException(f"Language {language.name} not supported for Spark EMR")
        if not self.session_started:
            self.get_logger().warning("Session not started. Cannot run a statement.")
            raise NoSessionException("Session not started. Cannot run a statement.")
        self._set_language(language)
        if self.debugging_helper and interactive_debugging:
            self.debugging_helper.prepare_statement(cell)
        try:
            if language == Language.sql:
                row_limit = self.sql_result_row_limit
                query_results = self.spark_magic.execute_sqlquery(
                    cell=cell,
                    samplemethod=None,
                    maxrows=row_limit,
                    samplefraction=None,
                    session=self.connection_name,
                    output_var=None,
                    quiet=False,
                    coerce=None,
                )
                if len(query_results) == row_limit:
                    SageMakerConnectionDisplay.write_msg(f"Query results have been limited to {row_limit} rows.")
                return query_results
            else:
                return self._execute_spark_with_output(cell, interactive_debugging=interactive_debugging)
        except Exception as e:
            self.handle_exception(e)

    def stop_session(self):
        try:
            if self.session_started:
                self.spark_magic.spark_controller.delete_session_by_name(self.connection_name)
                self.session_started = False
                self.endpoint = None
        except Exception as e:
            self.get_logger().error(f"Error stopping session. {e}")
            self.handle_exception(e)
        finally:
            self.post_session_stopped()

    def is_session_connectable(self):
        if not self.session_started:
            return False
        try:
            session = self._get_session()
            if session.status not in FINAL_STATUS:
                return True
        except Exception as e:
            self.get_logger().error(f"Error determining if session is connectable because of {e}")
            self.handle_exception(e)
        self.session_started = False
        return False

    def get_info(self):
        try:
            properties = conf.get_session_properties(self.language)
            info_sessions = self.spark_magic.spark_controller.get_all_sessions_endpoint(self.endpoint)
            return self._get_info_helper(properties, info_sessions)
        except Exception as e:
            self.handle_exception(e)

    def get_logs(self):
        try:
            livy_logs = self.spark_magic.spark_controller.get_logs(self.connection_name)
            if self.session_started:
                SageMakerConnectionDisplay.display(livy_logs)
            else:
                SageMakerConnectionDisplay.display("No logs yet.")
        except Exception as e:
            self.handle_exception(e)

    def _configure_core(self, cell):
        try:
            dictionary = json.loads(cell)
        except ValueError:
            SageMakerConnectionDisplay.send_error(f"Could not parse JSON object from input '{format(cell)}'")
            return

        if "auto_add_catalogs" in dictionary.keys():
            self._set_auto_add_catalogs(dictionary.pop("auto_add_catalogs"))

        self.config_dict.update(dictionary)

        SageMakerConnectionDisplay.display(f"The following configurations have been updated: {json.loads(cell)}")

    def _get_info_helper(self, properties, info_sessions=None):
        if self.session_started:
            current_session_id = self.spark_magic.spark_controller.get_session_id_for_client(
                self.connection_name
            )
            SageMakerConnectionDisplay.write_critical_msg(self._get_connection_info())
        else:
            current_session_id = None
        SageMakerConnectionDisplay.display(JSON(properties))
        self._print_endpoint_info(info_sessions, current_session_id)
        return properties

    def _get_connection_info(self):
        if self.connection_details and isinstance(self.connection_details, EmrOnEc2Connection):
            return CONNECTION_INFO_EMR_EC2_TEMPLATE.format(self.connection_details.cluster_id,
                                                           self.connection_details.runtime_role_arn)
        elif self.connection_details and isinstance(self.connection_details, EmrOnServerlessConnection):
            return CONNECTION_INFO_EMR_SERVERLESS_TEMPLATE.format(self.connection_details.application_id)

    def _print_endpoint_info(self, info_sessions, current_session_id):
        if info_sessions:
            info_sessions = sorted(info_sessions, key=lambda s: s.id)
            html = get_sessions_info_html(info_sessions, current_session_id)
            SageMakerConnectionDisplay.write_critical_msg(self.INFO_TABLE_MSG.format(self.connection_name))
            SageMakerConnectionDisplay.html(html)
        else:
            SageMakerConnectionDisplay.write_msg("No active sessions.")

    def _get_session(self):
        if (not self.session_started) or (not self.endpoint):
            raise NoSessionException(f"No session for {self.connection_name}")
        current_session_id = self.spark_magic.spark_controller.get_session_id_for_client(
            self.connection_name
        )
        info_sessions = self.spark_magic.spark_controller.get_all_sessions_endpoint(self.endpoint)
        for session in info_sessions:
            if session.id == current_session_id:
                return session
        raise NoSessionException(f"No session with id {current_session_id}")

    def _set_language(self, language: Language):
        livy_session = self.spark_magic.spark_controller.session_manager.get_session(self.connection_name)
        # if sql, we do not need to update the language,
        # because sql is not a supported language by Livy
        # sql will be translated to either pyspark or spark code when executing
        # so, we will continue to use the language that is already set in the Livy session
        if language == Language.sql:
            return
        livy_session.kind = LANGUAGE_LIVY_KIND_MAP.get(language)

    def _install_from_pip(self) -> any:
        raise NotImplementedError("_install_from_pip is not implemented yet")

    def _set_libs(self, properties) -> any:
        raise NotImplementedError("_set_lib is not implemented yet")

    # Adapted from https://github.com/jupyter-incubator/sparkmagic/blob/master/sparkmagic/sparkmagic/magics/sparkmagicsbase.py#L117
    # This function executes spark code, but rather than automatically placing the output to standard out, returns
    # the output, enabling communication from the spark compute to the local kernel. In particular, there
    # is no way to perform client-side rendering with the display magic without this change. This does not change the experience for the user
    # as the output is handled as part of the display magic and puts output to stdout. This change encompasses all previous
    # functionality while enabling parsing of the ultimate output
    def _execute_spark_with_output(self, cell, interactive_debugging: bool=True):
        success = False
        try:
            (success, out, mimetype) = self.spark_magic.spark_controller.run_command(Command(cell), self.connection_name)
        except Exception as e:
            self.handle_spark_error(str(e), interactive_debugging)
        if not success:
            if conf.shutdown_session_on_spark_statement_errors():
                self.spark_magic.spark_controller.cleanup()
            self.handle_spark_error(out, interactive_debugging)

        # INFER TYPE TO RETURN
        else:
            if isinstance(out, string_types):
                if mimetype == MIMETYPE_TEXT_HTML:
                    return out
                # strip additional single quotes added
                out = out.strip("'")

                # Check for special case of { "text/html": "<div>...</div>" }
                # which is return by Livy from IPython display or display_html
                # parse out the html and display it
                if out.startswith("{") and out.endswith("}"):  # PARSE TO DICT
                    # output will be in dict format (single quotes) so convert to JSON double quotes
                    json_out = out.replace("'", '"')
                    try:
                        out_dict = json.loads(json_out)
                        if MIMETYPE_TEXT_HTML in out_dict:
                            return out_dict[MIMETYPE_TEXT_HTML]
                        else:
                            return out
                    except:
                        return out
                elif out.startswith("[") and out.endswith("]"):  # PARSE TO DICT
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
            else:
                return out
        return out
