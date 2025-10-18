import abc
import logging
import re
import time
import uuid
from typing import Optional

from IPython import get_ipython

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import create_sts_client
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DATAZONE_DOMAIN_REGION, Language
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_renderer import BaseDisplayRenderer
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.sts_gateway import StsGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.utils.profile.aws_profile_helper import create_aws_profile_if_not_existent


class BaseSessionManager(metaclass=abc.ABCMeta):

    def __init__(self) -> None:
        # The limit for the number of rows that can be returned in a SQL query. Defaults to 10000.
        self.sql_result_row_limit = 10_000
        self._create_profile_if_not_existent()
        self.sts_client = create_sts_client(self.profile, DATAZONE_DOMAIN_REGION)
        self.sts_gateway = StsGateway(self.sts_client)
        self.debugging_helper: Optional[BaseDebuggingHelper] = None

    @abc.abstractmethod
    def create_session(self):
        """
        Create a new session
        """
        raise NotImplementedError('Must define create_session to use this BaseSessionManager')

    @abc.abstractmethod
    def run_statement(self, cell="", language: Optional[Language] = None, **kwargs):
        """
        Run a statement against the session
        :param cell: the code to run
        """
        raise NotImplementedError('Must define run_statement to use this BaseSessionManager')

    @abc.abstractmethod
    def stop_session(self):
        """
        Stop the session
        """
        raise NotImplementedError('Must define stop_session to use this BaseSessionManager')

    @abc.abstractmethod
    def is_session_connectable(self) -> bool:
        """
        Check if the session is connectable and in a valid status for running statement
        :return: true if the session is in a valid status, false otherwise
        """
        raise NotImplementedError('Must define is_session_connectable to use this BaseSessionManager')

    @abc.abstractmethod
    def _configure_core(self, cell: str):
        """
        To configure current compute to be connected and start a new session with applied configuration
        :param cell: the content to be applied for the session
        """

    def _replace_variables(self, input_string):
        def replace_match(match):
            variable_name = match.group(1)
            if not variable_name:
                raise ValueError(f"Empty variable reference found in: {input_string}")
            if variable_name not in get_ipython().user_ns:
                raise ValueError(f"Variable '{variable_name}' not found in user namespace")
            return str(get_ipython().user_ns[variable_name])

        pattern = r'\$\{([^}]*)\}'
        return re.sub(pattern, replace_match, input_string)

    def configure(self, cell: str, force: bool = False):
        """
        To configure current compute to be connected and start a new session with applied configuration
        :param cell: the content to be applied for the session
        :param force: a boolean to check if a user wants to force start a new session to apply configuration

        The invocation tree for %%configure magic is:
        connection magic -> base session manager -> configure -> configure_core ->
        specific session manager such as livy_session / glue_session

        Adding logic check here at base session manager makes more sense as variable detection should happen for all
        """
        hydrated_cell = self._replace_variables(cell)

        if self.is_session_connectable():
            if not force:
                SageMakerConnectionDisplay.send_error(
                    "A session has already been started. If you intend to recreate the "
                    "session with new configurations, please include the -f or --force argument.")
            else:
                self.stop_session()
                self._configure_core(hydrated_cell)
                self.create_session()
        else:
            self._configure_core(hydrated_cell)
        return

    def send_to_remote(self, local_var: str, remote_var: str, language=Language.python):
        # Not an abstract method because by default a session manager does not support this
        # only Spark session manager supports this for now.
        """
        Send a local variable in kernel's userspace to remote compute.
        e.g: for an EMR cluster, send a local variable to spark
        :param local_var: local variable name
        :param remote_var: remote variable name
        """
        raise NotImplementedError('Send_to_remote is not supported')

    def get_info(self):
        """
        Get information about the connected compute session
        """
        raise NotImplementedError('get_info is not supported for current session')

    def get_session_id(self):
        """
        Get the session ID of the connected compute session
        """
        raise NotImplementedError('get_session_id is not supported for current session')

    def get_status(self):
        """
        Get the status of the connected compute session
        """
        raise NotImplementedError('get_status is not supported for current session')

    def add_tags(self, tags: str):
        """
        Add tags to the connected compute session resources
        """
        raise NotImplementedError('add_tags is not supported for current session')

    def get_logs(self):
        """
        Gets the current session's Livy logs
        """
        raise NotImplementedError('get_logs is not supported for current session')

    def matplot(self, line: str):
        """
        Using matplotlib to plot the current session's plot'
        """
        raise NotImplementedError('matplot is not supported for current session')

    def set_session_id_prefix(self, prefix: str, force: bool = False):
        """
        Sets the session ID prefix of the session to be created
        """
        raise NotImplementedError('set_session_id_prefix is not supported for current session')

    def set_number_of_workers(self, number: str, force: bool = False):
        """
        Sets the number of workers of the session to be created
        """
        raise NotImplementedError('set_number_of_workers is not supported for current session')

    def set_worker_type(self, type: str, force: bool = False):
        """
        Sets the worker type of the session to be created
        """
        raise NotImplementedError('set_worker_type is not supported for current session')

    def set_session_type(self, session_type: str, force: bool = False):
        """
        Sets the session type of the session to be created. Acceptable session_type values are: streaming and etl.
        """
        raise NotImplementedError('set_session_type is not supported for current session')

    def set_glue_version(self, glue_version: str, force: bool = False):
        """
        Sets the glue version of the session to be created
        """
        raise NotImplementedError('set_glue_version is not supported for current session')

    def set_idle_timeout(self, idle_timeout: str, force: bool = False):
        """
        Sets the idle timeout value of the session to be created
        """
        raise NotImplementedError('set_idle_timeout is not supported for current session')

    def spark_conf(self, spark_conf: str, force: bool = False):
        """
        Sets the spark configuration value of the session to be created
        """
        raise NotImplementedError('spark_conf is not supported for current session')

    def get_logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(__name__)
        return self._logger

    def _create_profile_if_not_existent(self):
        if self.connection_details.connection_id:
            create_aws_profile_if_not_existent(self.connection_details.connection_id)
            self.profile = self.connection_details.connection_id
        else:
            self.profile = None

    def create_display_renderer(self, **kwargs) -> BaseDisplayRenderer:
        display_uuid = f"{int(time.time() * 1000)}_{uuid.uuid4().hex}"
        kwargs.setdefault('display_uuid', display_uuid)
        kwargs.setdefault('display_compute_id', 'display_compute_' + display_uuid)
        kwargs.setdefault('last_line_execution', False)
        kwargs.setdefault('spark_session', False)
        kwargs.setdefault('size', 10_000)
        kwargs.setdefault('sampling_method', "head")
        kwargs.setdefault('columns', None)
        kwargs.setdefault('type_inference', False)
        kwargs.setdefault('plot_lib', "default")
        kwargs.setdefault('view', "all")
        kwargs.setdefault('spark_use_threshold', 1_000_000)
        kwargs.setdefault('max_sample', 1_000_000_000)
        kwargs.setdefault('graph_render_threshold', 1_000_000)
        kwargs.setdefault('storage', 'cell')
        kwargs.setdefault('enable_profiling', False)
        kwargs.setdefault('query_result_s3_suffix', self._construct_query_result_s3_suffix(display_uuid))
        return self._create_display_renderer(**kwargs)

    @abc.abstractmethod
    def _create_display_renderer(self, **kwargs) -> BaseDisplayRenderer:
        raise NotImplementedError('Must define _create_display_render to use this BaseSessionManager')

    def _construct_query_result_s3_suffix(self, data_uuid):
        return f"user/{self.sts_gateway.get_source_identity()}/query-result/{data_uuid}/"
