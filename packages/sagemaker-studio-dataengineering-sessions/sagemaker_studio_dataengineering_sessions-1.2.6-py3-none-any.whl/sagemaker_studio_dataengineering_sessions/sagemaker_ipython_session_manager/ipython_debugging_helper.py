"""
IPython debugging helper for SageMaker Studio Data Engineering Sessions.

This module provides a debugging helper for IPython sessions used in SageMaker Studio.
"""

import asyncio
import os
from collections import OrderedDict
from typing import Any, Dict, Set
import sys

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DEFAULT_DEBUGGING_DIR_PARENT

# Constants for code history
CODE_HISTORY_MAX_SIZE = 100000


class IpythonDebuggingHelper(BaseDebuggingHelper):
    """
    Debugging helper for IPython sessions.
    
    This class extends the BaseDebuggingHelper to provide IPython-specific debugging
    functionality.
    """
    
    def __init__(self):
        super().__init__()
        self.current_statement = None
    
    def prepare_session(self, **kwargs) -> None:
        """
        Prepare the IPython session for debugging.
        
        Args:
            **kwargs: Additional parameters.
        """
        pass
    
    def prepare_statement(self, statement: str, **kwargs) -> None:
        """
        Prepare a statement for debugging.
        
        Args:
            statement: The statement to prepare.
            **kwargs: Additional parameters.
        """
        pass
    
    def get_debugging_info_tasks(self, **kwargs) -> Dict[str, asyncio.Task]:
        """
        Get debugging information tasks for the IPython session.
        
        Args:
            **kwargs: Additional parameters.
            
        Returns:
            Dict[str, asyncio.Task]: A dictionary of tasks to get debugging information.
        """
        # IPython doesn't have specific API requests like Spark or Database sessions
        # Return an empty task map as there are no specific tasks to run
        return {}

    def get_allowlisted_fields(self) -> Set[str]:
        """Return set of fields that are allowed to be logged.

        For IPython sessions, we only allow basic debugging information.

        Returns:
            Set[str]: Set of field names that are allowed to be included in logs.
        """
        return {
            "failed_cell_id",
            "failed_cell_type",
            "error_message",
            "session_type",
        }
    
    def get_cell_type(self) -> str:
        """
        Get the cell type for debugging information.
        
        Returns:
            str: The cell type.
        """
        return "ipython"
    
    def get_sop_file_name(self) -> str:
        """
        Get the name of the SOP file for debugging.
        
        Returns:
            str: The name of the SOP file.
        """
        return "ipython_debugging_sop.txt"
    
    def get_source_sop_path(self) -> str:
        """
        Get the source path of the SOP file for debugging.
        
        Returns:
            str: The source path of the SOP file.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "prompts", self.get_sop_file_name())
    
    def get_target_sop_path(self) -> str:
        """
        Get the target path of the SOP file for debugging.
        
        Returns:
            str: The target path of the SOP file.
        """
        return os.path.join(DEFAULT_DEBUGGING_DIR_PARENT, self.get_sop_file_name())
    
    def get_additional_debugging_info(self) -> Dict[str, Any]:
        """
        Get additional debugging information specific to the IPython session.
        
        Returns:
            Dict[str, Any]: Additional debugging information.
        """
        return {}
    
    def clean_up(self):
        """
        Clean up resources used by the debugging helper.
        """
        # No specific resources to clean up for IPython sessions
        pass
