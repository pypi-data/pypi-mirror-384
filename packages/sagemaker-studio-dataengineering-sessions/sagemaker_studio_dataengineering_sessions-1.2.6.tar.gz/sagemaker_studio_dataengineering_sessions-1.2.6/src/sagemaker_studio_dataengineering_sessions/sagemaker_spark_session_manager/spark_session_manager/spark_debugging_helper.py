import abc
import datetime
import json
import asyncio
import os
from collections import OrderedDict
import time

from typing import Any, Dict, Set
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DEFAULT_DEBUGGING_DIR_PARENT
import sys



TUNING_SPARK_PROPERTIES = [  
    "spark.executor.cores",
    "spark.executor.memory",
    "spark.executor.instances",
    "spark.driver.memory",
    "spark.driver.cores",
    "spark.default.parallelism", 
    "spark.sql.shuffle.partitions",
    "spark.dynamicAllocation.enabled",
    "spark.memory.fraction",
    "spark.memory.storageFraction",
    "spark.storage.memoryMapThreshold",
    "spark.serializer",
    "spark.shuffle.compress",
    "spark.shuffle.file.buffer",
    "spark.speculation",
    "spark.speculation.interval",
    "spark.speculation.multiplier"
]

GET_SPARK_CONFIGURATIONS = "get_spark_configurations"
GET_SPARK_FAILED_TASKS_DETAILS = "get_spark_failed_task_details"
GET_SPARK_ALL_EXECUTORS = "get_spark_all_executors"
GET_SPARK_FAILED_JOBS = "get_spark_failed_jobs"
GET_SPARK_UNKNOWN_JOBS = "get_spark_unknown_jobs"
GET_RESOURCE_MANAGER_YARN_DIAGNOSTIC = "get_resource_manager_yarn_diagnostic"

CODE_HISTORY_MAX_SIZE = 100000

class SparkDebuggingHelper(BaseDebuggingHelper, metaclass=abc.ABCMeta):
    
    def __init__(self):
        super().__init__()
        self.spark_ui_base_url = None
        self.code_history = OrderedDict()
        self.request_session = None
        self.session_stopped = False
        
    @abc.abstractmethod
    def prepare_session(self, **kwargs) -> None:
        pass
    
    def prepare_statement(self, statement: str, **kwargs) -> None:
        self.code_history[str(datetime.datetime.now())] = statement
        while self.code_history and sys.getsizeof(self.code_history) > CODE_HISTORY_MAX_SIZE:
            self.code_history.popitem(last=False)

    
    def get_spark_configurations(self, application_id: str | None) -> Any:
        response_json = self._make_spark_api_request(GET_SPARK_CONFIGURATIONS, application_id=application_id)
        spark_configs = {}
        if response_json and 'sparkProperties' in response_json:
            for i, prop in enumerate(response_json['sparkProperties']):
                if prop[0] in TUNING_SPARK_PROPERTIES:
                    spark_configs[prop[0]] = prop[1]
        return spark_configs
        
    def get_spark_failed_task_details(self, application_id: str | None) -> Any: 
        result = self._make_spark_api_request(GET_SPARK_FAILED_TASKS_DETAILS, application_id=application_id)
        
        # Remove 'host' and 'executorLogs' fields from each task in the tasks dictionary
        if result and isinstance(result, list):
            for stage in result:
                if 'tasks' in stage and isinstance(stage['tasks'], dict):
                    for task_id, task in stage['tasks'].items():
                        if 'host' in task:
                            del task['host']
                        if 'executorLogs' in task:
                            del task['executorLogs']
        
        return result
    
    def get_spark_all_executors(self, application_id: str | None) -> Any:
        result = self._make_spark_api_request(GET_SPARK_ALL_EXECUTORS, application_id=application_id)
        
        # Remove 'attributes', 'hostPort', and 'executorLogs' fields from each executor
        if result and isinstance(result, list):
            for executor in result:
                if 'attributes' in executor:
                    del executor['attributes']
                if 'hostPort' in executor:
                    del executor['hostPort']
                if 'executorLogs' in executor:
                    del executor['executorLogs']
        
        return result
    
    def get_spark_failed_jobs(self, application_id: str | None) -> Any:
        return self._make_spark_api_request(GET_SPARK_FAILED_JOBS, application_id=application_id)
    
    def get_spark_unknown_jobs(self, application_id: str | None) -> Any:
        return self._make_spark_api_request(GET_SPARK_UNKNOWN_JOBS, application_id=application_id)
    
    def get_resource_manager_yarn_diagnostic(self, application_id: str | None) -> Any:
        result = self._make_spark_api_request(GET_RESOURCE_MANAGER_YARN_DIAGNOSTIC, application_id=application_id)
        filtered_result = {}
        if result and 'app' in result and 'diagnostics' in result['app']:
            filtered_result["yarn_resouce_manager_diagnostics"] = result['app']['diagnostics'] 
        return filtered_result
    
    def _make_spark_api_request(self, request_name: str, application_id: str|None) -> Any:
        if self.request_session is None or self.spark_ui_base_url is None:
            try:
                future = self.prepare_session_in_seperate_thread()
                # Wait for the future to complete
                future.result()
            except Exception as e:
                self.get_logger().error(f"Error preparing session: {e}")
        
        if self.request_session is None:
            self.get_logger().error("Failed to initialize request_session")
            return {}
            
        if self.spark_ui_base_url is None:
            self.get_logger().error("Failed to initialize spark_ui_base_url")
            return {}
            
        try:
            response = self.request_session.get(self._get_url_from_task_name(request_name, application_id))
            
            if response.status_code == 403:
                self.get_logger().info("Received 403 Forbidden, refreshing session and retrying...")
                response.close() 
                
                try:
                    future = self.prepare_session_in_seperate_thread()
                    future.result()
                except Exception as e:
                    self.get_logger().error(f"Error preparing session: {e}")
                
                if self.request_session is None:
                    self.get_logger().error("Failed to initialize request_session on retry")
                    return {}
                    
                response = self.request_session.get(self._get_url_from_task_name(request_name, application_id))
            
            # Check for 400 status code, in this case it could mean that the application was terminated because of error
            # retry for prepare_session with session_stpped flag on
            if response.status_code == 400:
                self.get_logger().error(f"HTTP error: {response.status_code}, {response.reason}")
                response.close()
                try:
                    self.session_stopped = True
                    future = self.prepare_session_in_seperate_thread()
                    future.result()
                except Exception as e:
                    self.get_logger().error(f"Error preparing session: {e}")
                
                if self.request_session is None:
                    self.get_logger().error("Failed to initialize request_session on retry")
                    return {}
                    
                response = self.request_session.get(self._get_url_from_task_name(request_name, application_id))
            # this could happen when SHS is not yet having the application listed yet. retry with timeout
            if response.status_code == 404:
                max_retries = 3 
                retry_count = 0
                retry_interval = 10  # seconds
                
                while response.status_code == 404 and retry_count < max_retries:
                    self.get_logger().info(f"Received 404 error, retrying in {retry_interval}s (attempt {retry_count + 1}/{max_retries})...")
                    response.close()
                    time.sleep(retry_interval)
                    retry_count += 1
                    response = self.request_session.get(self._get_url_from_task_name(request_name, application_id))
                
                if response.status_code == 404:
                    self.get_logger().error(f"Still receiving 404 error after {max_retries} retries")
            
            if response.status_code != 200:
                self.get_logger().error(f"HTTP error: {response.status_code}, {response.reason}")
                response.close()
                return {}
                
            content = response.content
            result = json.loads(content)
            response.close()
            return result
        except Exception as e:
            self.get_logger().error(f"Error in {request_name}: {e}")
            return {}
        
    def get_debugging_info_tasks(self, **kwargs) -> Dict[str, asyncio.Task]:
        application_id = kwargs.get('application_id') if kwargs else None
        task_map = {}
        
        # Define the tasks to be created with their corresponding methods
        task_definitions = {
            "spark_selected_configurations": self.get_spark_configurations,
            "spark_failed_task_details": self.get_spark_failed_task_details,
            "spark_all_executors": self.get_spark_all_executors,
            "spark_failed_jobs": self.get_spark_failed_jobs,
            "spark_unknown_jobs": self.get_spark_unknown_jobs,
            "resource_manager_yarn_diagnostic": self.get_resource_manager_yarn_diagnostic
        }
        
        # Create tasks with exception handling for each task
        for task_name, method in task_definitions.items():
            try:
                task_map[task_name] = asyncio.create_task(asyncio.to_thread(method, application_id))
            except Exception as e:
                self.get_logger().error(f"Error creating task for {task_name}: {e}")
                # Create a task that returns an empty dictionary in case of an exception
                async def empty_task():
                    return {}
                task_map[task_name] = asyncio.create_task(empty_task())
        
        return task_map

    def get_allowlisted_fields(self) -> Set[str]:
        return {
            # Basic information
            "failed_cell_id",
            "failed_cell_type",
            "error_message",
            "session_type",

            # Spark-specific information
            "spark_selected_configurations",
            "spark_failed_task_details",
            "spark_all_executors",
            "spark_failed_jobs",
            "spark_unknown_jobs",
            "resource_manager_yarn_diagnostic"
        }

    @abc.abstractmethod
    def _get_url_from_task_name(self, task_name: str, application_id: str | None) -> str:
        pass
    
    def get_cell_type(self) -> str:
        return "spark"
    
    def get_sop_file_name(self) -> str:
        return "spark_debugging_sop.txt"
    
    def get_source_sop_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "prompts", self.get_sop_file_name())
    
    def get_target_sop_path(self) -> str:
        return os.path.join(DEFAULT_DEBUGGING_DIR_PARENT, self.get_sop_file_name())
    
    def get_additional_debugging_info(self) -> Dict[str, Any]:
        """
        Get additional debugging information specific to the spark session.
        
        Returns:
            Dict[str, Any]: Additional debugging information.
        """
        return {
            "latest_code_history": self.code_history
        }
    
    def clean_up_request_session(self):
        if self.request_session is not None:
            self.request_session.close()
            self.request_session = None
            
    def clean_up(self):
        self.clean_up_request_session()
