__version__ = '0.0.1'
import logging

from .cell_actions import CellActions
from .completers.connection_name_completers import connection_name_matcher
from .completers.variable_reference_completers import variable_reference_matcher
from .sagemaker_connection_magic import SageMakerConnectionMagic
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.logger_utils import setup_logger
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import SageMakerToolkitUtils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
setup_logger(logger, "SageMakerConnectionMagic", "connection_magic")

def load_ipython_extension(ipython):
    ipython.register_magics(SageMakerConnectionMagic)
    ipython.Completer.custom_matchers.append(connection_name_matcher)
    ipython.Completer.custom_matchers.append(variable_reference_matcher)
    ipython.events.register('post_run_cell', CellActions.post_run_cell_actions)
    ipython.events.register('pre_run_cell', CellActions.pre_cell_run_actions)
    SageMakerToolkitUtils.get_connection_type_mapping()
