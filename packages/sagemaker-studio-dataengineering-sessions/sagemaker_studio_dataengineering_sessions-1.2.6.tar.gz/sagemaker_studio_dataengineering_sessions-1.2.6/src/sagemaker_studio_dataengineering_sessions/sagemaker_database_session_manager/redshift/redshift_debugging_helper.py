import asyncio
import logging
import os
from typing import Any, Dict, Optional, TYPE_CHECKING

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DEFAULT_DEBUGGING_DIR_PARENT, DatabaseType
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.sql_workbench_gateway import SqlWorkbenchGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.database_debugging_helper import DatabaseDebuggingHelper

if TYPE_CHECKING:
    from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.redshift_session import RedshiftSession

logger = logging.getLogger(__name__)


class RedshiftDebuggingHelper(DatabaseDebuggingHelper):
    def __init__(self, session: "RedshiftSession"):
        super().__init__()
        self.session = session
        
    
    def prepare_session(self, **kwargs) -> None:
        super().prepare_session(**kwargs)
    
    def prepare_statement(self, statement: str, **kwargs) -> None:
        super().prepare_statement(statement, **kwargs)
