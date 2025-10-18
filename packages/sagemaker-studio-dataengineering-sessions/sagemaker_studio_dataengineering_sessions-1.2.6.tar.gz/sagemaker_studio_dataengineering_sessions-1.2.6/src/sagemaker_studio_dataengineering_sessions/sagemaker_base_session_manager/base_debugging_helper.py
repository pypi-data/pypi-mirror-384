"""
Base debugging helper interface for SageMaker Studio Data Engineering Sessions.

This module provides an abstract base class that defines the interface for debugging helpers
used across different session managers.
"""

import abc
import logging
import threading
import concurrent.futures
import asyncio
import json
import os
import shutil
import time
from concurrent.futures import Future
from typing import Any, Dict, Optional, Set
from IPython.display import display
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers.log_serializer import LogSerializer


from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import (
    DEFAULT_DEBUGGING_DIR_PARENT, 
    DEFAULT_DEBUGGING_DIR_TEMPLATE, 
    SYMLINK_DEBUGGING_DIR_PARENT, 
    SYMLINK_DEBUGGING_DIR_TEMPLATE,
    DEBUGGING_INFO_CENTRAL_LOG_DIR,
    DEBUGGING_INFO_CENTRAL_LOG_FILE,
    METRICS_NAMESPACE
)


class BaseDebuggingHelper(metaclass=abc.ABCMeta):

    """
    Abstract base class for debugging helpers.
    
    This interface defines the contract that all debugging helper implementations
    must follow, providing methods for retrieving and writing debugging information.
    """
    
    def __init__(self):
        self._prepare_session_future: Optional[Future] = None
        self._prepare_session_lock = threading.Lock()
        self.session = None
        self.current_cell_run_id = None

    @abc.abstractmethod
    def prepare_session(self, **kwargs):
        raise NotImplementedError("prepare_session must be implemented")
        
    def prepare_session_in_seperate_thread(self, **kwargs) -> Future:
        """
        Ensures that prepare_session is executed only once at a time for this instance.
        If a session preparation is already in progress for this instance, it returns the existing Future.
        Otherwise, it creates a new Future and runs prepare_session in a separate thread.
        
        Returns:
            Future: A Future object that will be completed when the session preparation is done.
        """
        
        # Use a lock to ensure thread safety when checking and setting _prepare_session_future
        with self._prepare_session_lock:
            # Check if there's already a Future in progress for this instance
            if self._prepare_session_future is not None and not self._prepare_session_future.done():
                self.get_logger().info("Session preparation already in progress for this instance, returning existing Future")
                return self._prepare_session_future
            
            # Create a new Future using ThreadPoolExecutor
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            self._prepare_session_future = executor.submit(self.prepare_session, **kwargs)
            # Make sure to shutdown the executor when the future is done
            self._prepare_session_future.add_done_callback(lambda _: executor.shutdown(wait=False))
            
            return self._prepare_session_future

    @abc.abstractmethod
    def prepare_statement(self, statement: str, **kwargs) -> None:
        raise NotImplementedError("prepare_session must be implemented")

    def get_logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(__name__)
        return self._logger
    
    def get_notebook_path(self) -> str:
        """
        Get the path to the current notebook.
        
        Returns:
            str: The path to the current notebook.
        """
        # Ref: https://github.com/jupyter-server/jupyter_server/pull/679/files
        notebook_path = os.getenv('JPY_SESSION_NAME')
        if notebook_path and os.path.exists(notebook_path):
            return notebook_path
        else:
            return ""
    
    @abc.abstractmethod
    def get_debugging_info_tasks(self, **kwargs) -> Dict[str, asyncio.Task]:
        """
        Get debugging information tasks for the session.
        
        Args:
            **kwargs: Additional parameters.
            
        Returns:
            Dict[str, asyncio.Task]: A dictionary of tasks to get debugging information.
        """
        raise NotImplementedError("get_debugging_info_tasks must be implemented")

    @abc.abstractmethod
    def get_allowlisted_fields(self) -> Set[str]:
        """Return set of fields that are allowed to be logged.

        Returns:
            Set[str]: Set of field names that are allowed to be included in logs.
        """
        raise NotImplementedError("get_allowlisted_fields must be implemented")
    
    def get_session_type_name(self) -> str:
        """
        Get the name of the session type for debugging information.
        
        Returns:
            str: The name of the session type.
        """
        return str(type(self.session)).split(".")[-1].split("'")[0] if self.session else "python_3"
    
    def get_cell_type(self) -> str:
        """
        Get the cell type for debugging information.
        
        Returns:
            str: The cell type (e.g., "database", "spark").
        """
        raise NotImplementedError("get_cell_type must be implemented")
    
    @abc.abstractmethod
    def get_sop_file_name(self) -> str:
        """
        Get the name of the SOP file for debugging.
        
        Returns:
            str: The name of the SOP file (e.g., "database_debugging_sop.txt").
        """
        raise NotImplementedError("get_sop_file_name must be implemented")
    
    @abc.abstractmethod
    def get_source_sop_path(self) -> str:
        """
        Get the source path of the SOP file for debugging.
        
        Returns:
            str: The source path of the SOP file.
        """
        raise NotImplementedError("get_source_sop_path must be implemented")
    
    @abc.abstractmethod
    def get_target_sop_path(self) -> str:
        """
        Get the target path of the SOP file for debugging.
        
        Returns:
            str: The target path of the SOP file.
        """
        raise NotImplementedError("get_target_sop_path must be implemented")
    
    @abc.abstractmethod
    def get_additional_debugging_info(self) -> Dict[str, Any]:
        """
        Get additional debugging information specific to the session type.
        
        Returns:
            Dict[str, Any]: Additional debugging information.
        """
        raise NotImplementedError("get_additional_debugging_info must be implemented")
    
    async def _get_debugging_info_async(self, **kwargs):
        """
        Get debugging information asynchronously.
        
        Args:
            **kwargs: Additional parameters.
            
        Returns:
            Dict[str, Any]: A dictionary containing debugging information.
        """
        task_map = self.get_debugging_info_tasks(**kwargs)
        result_map = {}
        
        # Process each task individually and handle exceptions for each task separately
        for key, task in task_map.items():
            try:
                result_map[key] = await task
            except Exception as e:
                # If an exception occurs for this task, only set this task's result to an empty dictionary
                self.get_logger().error(f"Error in _get_debugging_info_async for task {key}: {e}")
                result_map[key] = {}
        
        return result_map
    
    def _write_debugging_info_sync(self, cell_id: str, **kwargs) -> bool:
        """
        Write debugging information synchronously.
        
        Args:
            cell_id: The ID of the cell that triggered the debugging.
            **kwargs: Additional parameters.
            
        Returns:
            bool: True if the debugging information was written successfully.
        """
        directory = kwargs.get('directory', DEFAULT_DEBUGGING_DIR_TEMPLATE.format(cell_id=cell_id))
        error_message = kwargs.get('error_message') if kwargs else ""
        cell_content = kwargs.get('cell_content') if kwargs else ""
        self.get_logger().info(f"Writing debugging info for cell {cell_id}")
        
        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.chmod(directory, 0o755)
            
        success_path = f"{directory}/.success" 
        result_map = asyncio.run(self._get_debugging_info_async(**kwargs))
        
        debugging_info = {
            "path_to_notebook": self.get_notebook_path(),
            "failed_cell_id": cell_id,
            "failed_cell_type": self.get_cell_type(),
            "failed_cell_content": cell_content,
            "error_message": error_message,
            "session_type": self.get_session_type_name(),
            **self.get_additional_debugging_info(),
            **result_map
        }
        
        path = f"{directory}/debugging_info.json"
        with open(path, "w") as f:
            json.dump(debugging_info, f, indent=4)
        os.chmod(path, 0o644)

        self._write_to_central_log(debugging_info)

        with open(success_path, "w") as f:
            pass
        os.chmod(success_path, 0o644)

        return True

    def _write_to_central_log(self, debugging_info: dict):
        allowed_fields = self.get_allowlisted_fields()
        filtered_info = {k: v for k, v in debugging_info.items() if k in allowed_fields}
        metrics_context = MetricsContext.empty()
        metrics_context.namespace = METRICS_NAMESPACE
        metrics_context.should_use_default_dimensions = False

        dimensions = {
            "SessionType": filtered_info.get("session_type") or "UNKNOWN",
            "CellType": filtered_info.get("failed_cell_type") or "UNKNOWN"
        }
        metrics_context.put_dimensions(dimensions)
        self.get_logger().info(f"Set dimensions: {dimensions}")
        dimension_keys = {"session_type", "failed_cell_type"}
        for key, value in filtered_info.items():
            if key not in dimension_keys:
                metrics_context.set_property(key, value)
        try:
            logger = self._setup_debugging_info_logger()
            entry_count = 0
            for serialized_content in LogSerializer.serialize(metrics_context):
                if serialized_content:
                    logger.info(serialized_content)
                    entry_count += 1
            self.get_logger().info(f"Wrote {entry_count} entries to central log")
        except Exception as e:
            self.get_logger().warning(f"Failed to write to central log: {e}")

    def _setup_debugging_info_logger(self):
        """Setup logger for central debugging information."""
        log_path = os.path.join(DEBUGGING_INFO_CENTRAL_LOG_DIR, DEBUGGING_INFO_CENTRAL_LOG_FILE)
        os.makedirs(DEBUGGING_INFO_CENTRAL_LOG_DIR, mode=0o755, exist_ok=True)
        logger = logging.getLogger('debugging_info_logger')
        handler = logging.FileHandler(log_path, 'a')
        logger.addHandler(handler)
        os.chmod(log_path, 0o644)
        return logger


    def write_debugging_info(self, cell_id: str, **kwargs):
        """
        Write debugging information for a cell.
        
        Args:
            cell_id: The ID of the cell that triggered the debugging.
            **kwargs: Additional parameters.
        """
        
        # Import CellActions here to avoid possible circular import
        from sagemaker_studio_dataengineering_sessions.sagemaker_connection_magic.cell_actions import CellActions
        self.current_cell_run_id = CellActions.cell_run_id
        
        # Ensure the DEFAULT_DEBUGGING_DIR_PARENT exists
        if not os.path.exists(DEFAULT_DEBUGGING_DIR_PARENT):
            os.makedirs(DEFAULT_DEBUGGING_DIR_PARENT)
            os.chmod(DEFAULT_DEBUGGING_DIR_PARENT, 0o755)
            
        # Copy the SOP file from prompts directory to target path
        sop_file_name = self.get_sop_file_name()
        source_sop_path = self.get_source_sop_path()
        target_sop_path = self.get_target_sop_path()
        
        if not os.path.exists(target_sop_path) and os.path.exists(source_sop_path):
            shutil.copy(source_sop_path, target_sop_path)
            os.chmod(target_sop_path, 0o644)
            self.get_logger().info(f"Copied {sop_file_name} to {target_sop_path}")
        
        self._symlink_if_not_exist(DEFAULT_DEBUGGING_DIR_PARENT, SYMLINK_DEBUGGING_DIR_PARENT)
        self.get_logger().info(f"Starting asynchronous write of debugging info for cell {cell_id}...")
        directory = kwargs.get('directory', DEFAULT_DEBUGGING_DIR_TEMPLATE.format(cell_id=cell_id))

                
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.chmod(directory, 0o755)
        
        # Clean up old .success file if it exists
        success_path = f"{directory}/.success"
        if os.path.exists(success_path):
            os.remove(success_path)
        
        # Create a daemon thread to run the synchronous method
        daemon_thread = threading.Thread(
            target=self._write_debugging_info_sync,
            args=(cell_id,),
            kwargs=kwargs,
            daemon=True
        )
        daemon_thread.start()
        return
    
    def _symlink_if_not_exist(self, source_path: str, target_path: str) -> None:
        """
        Ensure that a symlink exists from source_path to target_path.
        
        Args:
            source_path: The source path.
            target_path: The target path.
        """
        # First, ensure source directory exists
        if not os.path.exists(source_path):
            os.makedirs(source_path)
            os.chmod(source_path, 0o755)
            self.get_logger().info(f"Created source directory: {source_path}")
            
        symlink_needs_update = False
        
        if os.path.islink(target_path):
            try:
                current_source = os.readlink(target_path)
                if current_source != source_path:
                    self.get_logger().info(f"Symlink points to incorrect destination: {current_source}, updating...")
                    symlink_needs_update = True
            except OSError as e:
                self.get_logger().warning(f"Error reading symlink: {e}, will recreate it")
                symlink_needs_update = True
        else:
            symlink_needs_update = True
            
        if symlink_needs_update:
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            os.symlink(src=source_path, dst=target_path, target_is_directory=True)
            self.get_logger().info(f"Created symlink from {source_path} to {target_path}")
        else:
            self.get_logger().info(f"Symlink from {source_path} to {target_path} already exists and is correct")
    
    @abc.abstractmethod
    def clean_up(self):
        """
        Clean up resources used by the debugging helper.
        
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError("clean_up must be implemented")


