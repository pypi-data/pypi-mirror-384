import logging

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.logger_utils import setup_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
setup_logger(logger, "SageMakerIpythonLabSessionManager", "connection_magic")
