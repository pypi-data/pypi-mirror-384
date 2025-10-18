import logging
import os
import uuid
from typing import Optional

from IPython.display import display

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_session_manager import BaseSessionManager
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import SYMLINK_DEBUGGING_DIR_PARENT, SYMLINK_DEBUGGING_DIR_TEMPLATE
from sagemaker_studio_dataengineering_sessions.sagemaker_ipython_session_manager.ipython_debugging_helper import IpythonDebuggingHelper

logger = logging.getLogger(__name__)

class CellActions:
    """
    Static class that handles IPython cell actions for SageMaker Studio Data Engineering Sessions.
    This class encapsulates the functionality for pre-cell and post-cell run actions.
    """
    
    # Class variables
    default_ipython_debugging_helper = IpythonDebuggingHelper()
    cell_run_id: Optional[str] = None
    # connection_magic will set this value to current session manager
    current_session_manager: Optional[BaseSessionManager] = None
    
    @classmethod
    def pre_cell_run_actions(cls, info):
        """
        Handle pre-cell run actions.
        
        Args:
            info: IPython cell info object
        """
        cls.cell_run_id = str(uuid.uuid4())
    
    @classmethod
    def post_run_cell_actions(cls, result):
        """
        Handle post-run cell actions, particularly for error cases.
        
        This function is registered as an IPython post_run_cell event handler.
        When a cell execution results in an error, it:
        1. Captures debugging information
        2. Determines the appropriate debugging helper
        3. Extracts magic command information if present
        4. Displays interactive debugging information for the frontend
        
        Args:
            result: IPython execution result object containing cell execution information
        """
        # Early return if no error occurred during execution
        if not result.error_in_exec:
            return
        
        # Extract basic information from the result
        cell_id = result.info.cell_id
        raw_cell = result.info.raw_cell
        error_message = result.error_in_exec

        # Set up default debugging values
        debugging_info_folder = SYMLINK_DEBUGGING_DIR_TEMPLATE.format(cell_id=cell_id)
        debugging_helper = cls.default_ipython_debugging_helper
        magic_command = "no_magic"
        
        if cls.current_session_manager is not None and cls._is_valid_session_manager_for_cell(cls.current_session_manager, cell_id):
            debugging_helper = cls.current_session_manager.debugging_helper
            magic_command = cls._extract_magic_command(raw_cell)
        else:
            # If debugging folder doesn't exist, write debugging info using the default helper
            debugging_helper.write_debugging_info(
                cell_id=cell_id,
                cell_content=raw_cell,
                magic_command="no_magic",
                error_message=str(error_message)
            )

        # Display interactive debugging information for the frontend
        cls._display_debugging_info(
            cell_id=cell_id,
            magic_command=magic_command,
            debugging_helper=debugging_helper,
            debugging_info_folder=debugging_info_folder
        )
        cls.current_session_manager = None

    @classmethod
    def _is_valid_session_manager_for_cell(cls, session_manager, cell_id):
        """
        Check if the session manager is valid and applicable for the given cell.
        
        Args:
            session_manager: The session manager to validate
            cell_id: The cell ID to check against
            
        Returns:
            bool: True if the session manager is valid for the cell, False otherwise
        """
        # First check if session_manager is None to avoid attribute access errors
        if session_manager is None:
            return False
            
        # Then check if it's the right type
        if not isinstance(session_manager, BaseSessionManager):
            return False
            
        # Now we can safely access debugging_helper
        if session_manager.debugging_helper is None:
            return False
            
        from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
        if not isinstance(session_manager.debugging_helper, BaseDebuggingHelper):
            return False
            
        # Finally check if the cell_id matches
        # Check if current_cell_run_id is None first to avoid TypeError
        if session_manager.debugging_helper.current_cell_run_id is None:
            return False
            
        return cls.cell_run_id == session_manager.debugging_helper.current_cell_run_id

    @classmethod
    def _extract_magic_command(cls, cell_content):
        """
        Extract magic command from cell content if present.
        
        Args:
            cell_content: The content of the cell
            
        Returns:
            str: The extracted magic command or "no_magic" if none found
        """
        if not cell_content or not cell_content.startswith("%%"):
            return "no_magic"
            
        space_index = cell_content.find(" ")
        if space_index != -1:
            return cell_content[:space_index]
        else:
            return cell_content

    @classmethod
    def _display_debugging_info(cls, cell_id, magic_command, debugging_helper, debugging_info_folder):
        """
        Display interactive debugging information for the frontend.
        
        Args:
            cell_id: The ID of the cell being debugged
            magic_command: The magic command used in the cell (if any)
            debugging_helper: The debugging helper to use
            debugging_info_folder: The folder containing debugging information
        """
        display({
            'application/sagemaker-interactive-debugging': {
                'cell_id': cell_id,
                "magic_command": magic_command,
                "session_type": debugging_helper.get_session_type_name(),
                "instruction_file": os.path.join(SYMLINK_DEBUGGING_DIR_PARENT, debugging_helper.get_sop_file_name()),
                'debugging_info_folder': debugging_info_folder
            }
        }, raw=True)
