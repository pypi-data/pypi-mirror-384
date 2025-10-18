import logging
import uuid

from IPython import get_ipython
from IPython.core.error import UsageError
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_connection import BaseConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_session_manager import BaseSessionManager
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import Language, PROJECT_S3_PATH, \
    DEFAULT_IPYTHON_NAME
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.debugging_utils import get_cell_content, get_cell_id
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import \
    LanguageNotSupportedException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import \
    SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.s3_manager.s3_variable_manager import S3VariableManager
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.utils.profile.aws_profile_helper import \
    set_aws_profile_and_region, reset_aws_profile_and_region
from sagemaker_studio_dataengineering_sessions.sagemaker_ipython_session_manager.display.ipython_display_renderer import \
    IpythonDisplayRenderer
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.ipython_display_compute import \
    IpythonDisplayCompute


class IpythonSession(BaseSessionManager):
    logger = logging.getLogger(__name__)

    def __init__(self, connection_name: str):
        if connection_name is not DEFAULT_IPYTHON_NAME:
            connection_id = SageMakerToolkitUtils.get_connection_id_from_connection_name(connection_name)
            connection_detail = SageMakerToolkitUtils.get_connection_detail_from_id(connection_id)
            self.connection_details = BaseConnection(
                connection_name=connection_name,
                connection_id=connection_id,
                region=connection_detail["physicalEndpoints"][0]["awsLocation"]["awsRegion"]
            )
        else:
            self.connection_details = BaseConnection(
                connection_name=connection_name,
                connection_id=None, # connection_id is only used as profile name for now.
                region=None # region is only used in profile setting for now 
            )
        super().__init__()
        self.connection_name = connection_name
        self.s3_variable_manager_name = None

    def create_session(self):
        # Jupyter Lab session is always available
        pass

    def run_cell(self, cell="", language=Language.python):
        if language != Language.python:
            raise LanguageNotSupportedException(f"Language {language.name} not supported for Local Python")
        try:
            self._set_aws_profile_and_region()
            get_ipython().run_cell(cell, cell_id=get_cell_id())
        except Exception as e:
            cell_id = get_cell_id()
            cell_content = get_cell_content()
            # Write debugging info if conditions are met
            if self.debugging_helper and cell_id and cell_content:
                self.debugging_helper.write_debugging_info(
                    cell_id=cell_id,
                    cell_content=cell_content,
                    magic_command="no_magic",
                    error_message=str(e)
                )
            raise e
        finally:
            reset_aws_profile_and_region()

    def run_statement(self, cell="", language=Language.python, mode="exec", **kwargs):
        if language != Language.python:
            raise LanguageNotSupportedException(f"Language {language.name} not supported for Local Python")
        interactive_debugging = kwargs.get('interactive_debugging', True)
        try:
            self._set_aws_profile_and_region()
            if mode == "exec":
                return get_ipython().ex(cell)
            elif mode == "eval":
                result = get_ipython().ev(cell)
                get_ipython().user_ns['_'] = result
                return result
        except Exception as e:
            cell_id = get_cell_id()
            cell_content = get_cell_content()
            # Write debugging info if conditions are met
            if self.debugging_helper and interactive_debugging and cell_id and cell_content:
                self.debugging_helper.write_debugging_info(
                    cell_id=cell_id, 
                    cell_content=cell_content,
                    magic_command="no_magic",
                    error_message=str(e)
                )
            raise e
                
        finally:
            reset_aws_profile_and_region()

    def stop_session(self):
        # Jupyter Lab session is always available
        pass

    def is_session_connectable(self) -> bool:
        # Jupyter Lab session is always available
        return True

    def _create_display_renderer(self, *args, **kwargs):
        try:
            display_compute_id = kwargs.get('display_compute_id')
            kwargs['df'] = get_ipython().user_ns.get(kwargs.get('df'))
            get_ipython().user_ns[display_compute_id] = IpythonDisplayCompute(project_s3_path=PROJECT_S3_PATH, *args, **kwargs)
            return IpythonDisplayRenderer(session_manager=self, data_uuid=kwargs.get('display_uuid'),
                                          display_magic_compute=display_compute_id, storage=kwargs.get('storage'),
                                          query_result_s3_suffix=kwargs.get('query_result_s3_suffix'),
                                          enable_profiling=kwargs.get("enable_profiling"))
        except Exception as e:
            self.get_logger().error(f"Could not create display compute: {e}")
            return None

    def _configure_core(self, cell: str):
        # Jupyter lab session doesn't support _configure_core
        raise NotImplementedError('configure magic is not by Local Python')

    def get_s3_store(self):
        if self.s3_variable_manager_name is None:
            try:
                s3_variable_manager_name = "_s3_variable_manager_" + uuid.uuid4().hex
                s3_variable_manager = S3VariableManager(project_s3_path=PROJECT_S3_PATH)
                get_ipython().user_ns[s3_variable_manager_name] = s3_variable_manager
                self.s3_variable_manager_name = s3_variable_manager_name
            except Exception as e:
                self.logger.error(f"Could not create s3 store handler: {e}")
                raise UsageError(f"Could not create s3 store handler: {e}")

        return self.s3_variable_manager_name

    def _set_aws_profile_and_region(self):
        if self.connection_details.connection_id and self.connection_details.region:
            set_aws_profile_and_region(self.connection_details.connection_id, self.connection_details.region)
        else:
            reset_aws_profile_and_region()
