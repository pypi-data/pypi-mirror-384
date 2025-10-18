import json
import os
from typing import TYPE_CHECKING

import requests
import subprocess

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import create_sagemaker_client
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DATAZONE_DOMAIN_REGION, SAGEMAKER_DOMAIN_ID, SAGEMAKER_SPACE_NAME
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.glue_gateway import GlueGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.sagemaker_gateway import SageMakerGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_connection import GlueConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_debugging_helper import GET_SPARK_ALL_EXECUTORS, GET_SPARK_CONFIGURATIONS, GET_SPARK_FAILED_JOBS, GET_SPARK_FAILED_TASKS_DETAILS, GET_SPARK_UNKNOWN_JOBS, SparkDebuggingHelper

if TYPE_CHECKING:
    from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_session import GlueSession

RUNNING_TOKEN = 'Spark History Server is running'
NOT_RUNNING_TOKEN = 'Spark History Server is not running'

class GlueDebuggingHelper(SparkDebuggingHelper):

    def __init__(self, gateway: GlueGateway, session: "GlueSession"):
        super().__init__()
        self.gateway = gateway
        self.session = session
        self.application_id = None
        self.sagemaker_gateway = SageMakerGateway(sagemaker_client=create_sagemaker_client(region=DATAZONE_DOMAIN_REGION))
        
    def prepare_session(self, **kwargs) -> None:
        self.get_logger().info(f"Preparing session for Glue session ID: {self.session.session_id}")
        
        if not self.session.session_id:
            self.get_logger().error("Session ID is not available")
            raise ValueError("Session ID is not available")
            
        session_details = self.gateway.get_interactive_session(self.session.session_id)
        status = session_details.get('Status')
        s3_path = session_details.get('DefaultArguments', {}).get("--spark-event-logs-path", "")
        if status in ['PROVISIONING', 'READY']:    
            dashboard_url = self.gateway.get_dashboard_url(self.session.session_id, 'SESSION')
            if dashboard_url:
                self.clean_up_request_session()
                self.request_session = requests.Session()
                response = self.request_session.get(dashboard_url, allow_redirects=True)
                self.spark_ui_base_url = response.url
            else:
                self.get_logger().error("Dashboard URL not available")
                raise RuntimeError("Dashboard URL not available")
        else:
            try:
                studio_space_id = self._get_studio_space_id()
                result = subprocess.run(
                    ['/usr/bin/sm-spark-cli', 'status'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode != 0:
                    self.get_logger().warning(f"sm-spark-cli status command failed with exit code {result.returncode}: {result.stderr}")
                    # Continue with starting the server even if status check fails
                    start_result = False
                else:
                    result_stdout = result.stdout
                    start_result = RUNNING_TOKEN in result_stdout
                
                if not start_result:
                    try:
                        result = subprocess.run(
                            ['/usr/bin/sm-spark-cli', 'stop'],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        start_process = subprocess.run(
                            ['/usr/bin/sm-spark-cli', 'start', s3_path],
                            input=f'{studio_space_id}\ny\n',
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if start_process.returncode != 0:
                            self.get_logger().error(f"Failed to start Spark History Server: {start_process.stderr}")
                            raise RuntimeError(f"Failed to start Spark History Server: {start_process.stderr}")
                        
                    except Exception as e:
                        self.get_logger().error(f"Error starting Spark History Server: {e}")
                        raise
                else:
                    self.get_logger().info(f"Skipped starting Spark History Server because it is already started")
                
                self.clean_up_request_session()
                self.request_session = requests.Session()
                self.spark_ui_base_url = "http://localhost:18080/"
                    
            except Exception as e:
                self.get_logger().error(f"Error checking Spark History Server status: {e}")
                raise
            
        if not self.application_id:
            try:
                self.application_id = self._get_application_id()
            except Exception as e:
                self.get_logger().error(f"failed to get application_id: {e}")
        
        self.get_logger().info(f"Prepare session for glue is done with application id: {self.application_id} and spark ui base url: {self.spark_ui_base_url}")

            
    def _get_url_from_task_name(self, task_name: str, application_id: str | None) -> str:
        if not application_id and not self.application_id:
            self.application_id = self._get_application_id()
        if application_id is None:
            application_id = self.application_id
        if task_name == GET_SPARK_UNKNOWN_JOBS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/jobs?status=unknown"
        elif task_name == GET_SPARK_FAILED_JOBS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/jobs?status=failed"
        elif task_name == GET_SPARK_FAILED_TASKS_DETAILS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/stages/?details=true&taskStatus=FAILED&?withSummaries=true"
        elif task_name == GET_SPARK_ALL_EXECUTORS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/allexecutors/"
        elif task_name == GET_SPARK_CONFIGURATIONS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/environment/"
        else:
            raise ValueError(f"Unknown task name: {task_name}")
        return target_url
    
    def _get_studio_space_id(self):
        try:
            response = self.sagemaker_gateway.describe_space(domain_id=SAGEMAKER_DOMAIN_ID, space_name=SAGEMAKER_SPACE_NAME)
            if "Url" in response:
                space_url = response["Url"]
                return space_url.split('.')[0].split('//')[1]
            else:
                self.get_logger().error("Url not found in response: %s", response)
                raise RuntimeError("Cannot find studio space id in describe space response")
        except Exception as e:
            self.get_logger().error("Error in _get_studio_space_id: %s", e)
            raise RuntimeError(f"Error in _get_studio_space_id: {e}")
        
    def _get_application_id(self) -> str:
        if self.spark_ui_base_url is None:
            raise ValueError("Spark UI base URL is not available")
        else:
            response = self.request_session.get(f"{self.spark_ui_base_url}api/v1/applications")
            response.raise_for_status()
            data = response.json()
            if len(data) == 0:
                raise RuntimeError("No application found in spark history server.")
            else:
                for app in data:
                    if app.get('name') == self.session.session_id:
                        return app['id']
                raise RuntimeError(f"No application found with name matching session ID: {self.session.session_id}")
