"""
Database debugging helper for SageMaker Studio Data Engineering Sessions.

This module provides a base class for database debugging helpers used across different
database session managers.
"""

import abc
import asyncio
import logging
import os
from typing import Any, Dict, Optional, Set

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DEFAULT_DEBUGGING_DIR_PARENT

# Constants for database API requests
GET_DATABASE_CONFIGURATION = "get_database_configuration"
GET_DATABASE_CONNECTION_STATUS = "get_database_connection_status"
GET_DATABASE_ERROR_DETAILS = "get_database_error_details"
GET_DATABASE_PERFORMANCE_METRICS = "get_database_performance_metrics"

logger = logging.getLogger(__name__)


class DatabaseDebuggingHelper(BaseDebuggingHelper, metaclass=abc.ABCMeta):
    """
    Abstract base class for database debugging helpers.
    
    This class extends the BaseDebuggingHelper to provide database-specific debugging
    functionality.
    """
    
    def __init__(self):
        super().__init__()
        self.current_statement = None
        
    def prepare_session(self, **kwargs) -> None:
        pass
    
    def prepare_statement(self, statement: str, **kwargs) -> None:
        self.current_statement = statement
    
    def get_query_plan(self) -> Any:
        result = {}
        if self.session:
            query_plan_query = f"EXPLAIN {self.current_statement}"
            try:
                result = self.session._run_query(query_plan_query, False)
            except Exception:
                self.get_logger().error("Unable to get query plan because of {e.__class__.__name__}: {e}")
        return result
    
    def get_debugging_info_tasks(self, **kwargs) -> Dict[str, asyncio.Task]:
        task_map = {
            "query_plan": asyncio.create_task(asyncio.to_thread(self.get_query_plan()))
        }
        return task_map

    def get_allowlisted_fields(self) -> Set[str]:
        return {
            "failed_cell_id",
            "failed_cell_type",
            "error_message",
            "session_type"
        }

    def get_cell_type(self) -> str:
        return "database"
    
    def get_sop_file_name(self) -> str:
        return "database_debugging_sop.txt"
    
    def get_source_sop_path(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "prompts", self.get_sop_file_name())
    
    def get_target_sop_path(self) -> str:
        return os.path.join(DEFAULT_DEBUGGING_DIR_PARENT, self.get_sop_file_name())
    
    def get_additional_debugging_info(self) -> Dict[str, Any]:
        return {}
    
    def clean_up(self):
        pass
        
