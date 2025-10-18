"""
EMR on Serverless debugging helper for SageMaker Studio Data Engineering Sessions.

This module provides debugging capabilities specific to EMR on Serverless sessions.
"""

import time
from typing import TYPE_CHECKING

import requests

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_serverless_gateway import EmrServerlessGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_connection import EmrOnServerlessConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_debugging_helper import GET_SPARK_ALL_EXECUTORS, GET_SPARK_CONFIGURATIONS, GET_SPARK_FAILED_JOBS, GET_SPARK_FAILED_TASKS_DETAILS, GET_SPARK_UNKNOWN_JOBS, SparkDebuggingHelper

if TYPE_CHECKING:
    from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_session import EmrOnServerlessSession


class EmrOnServerlessDebuggingHelper(SparkDebuggingHelper):
    """
    Debugging helper implementation for EMR on Serverless sessions.
    
    Provides methods to retrieve and write debugging information
    specific to EMR on Serverless applications.
    """

    def __init__(self, gateway: EmrServerlessGateway, session: "EmrOnServerlessSession"):
        super().__init__()
        self.gateway = gateway
        self.session = session
        
    def prepare_session(self, **kwargs) -> None:
        self.get_logger().info(f"prepare for session - EMR-S Application Id: {self.session.connection_details.application_id},  ExecutionRoleArn: {self.session.connection_details.runtime_role}, is session stopped: {self.session_stopped}")
        
        try:
            get_dashboard_for_emr_serverless_application_response = self.gateway.get_dashboard_for_emr_serverless_application(application_id=self.session.connection_details.application_id, job_run_id=self.session.get_app_id())
            if get_dashboard_for_emr_serverless_application_response['url']:
                self.clean_up_request_session()
                self.request_session = requests.Session()
                response = self.request_session.get(get_dashboard_for_emr_serverless_application_response['url'], allow_redirects=True)
                self.spark_ui_base_url = response.url
            else:
                self.get_logger().info("get_dashboard_for_emr_serverless_application does not have url")
        except Exception as e:
            self.get_logger().info(f"error in prepare_session: {e}")
            return
        
        # In case of session stopped (usually happens on a bad statement which causes error),
        # Need to wait until we got redirected to Spark History Server link.
        retry_count = 0
        while (self.session_stopped and not self.spark_ui_base_url.startswith("https://p-")):
            try:
                retry_count += 1
                if retry_count > 10:
                    break
                time.sleep(5)
                get_dashboard_for_emr_serverless_application_response = self.gateway.get_dashboard_for_emr_serverless_application(application_id=self.session.connection_details.application_id, job_run_id=self.session.get_app_id())
                if get_dashboard_for_emr_serverless_application_response['url']:
                    self.clean_up_request_session()
                    self.request_session = requests.Session()
                    response = self.request_session.get(get_dashboard_for_emr_serverless_application_response['url'], allow_redirects=True)
                    self.spark_ui_base_url = response.url
                else:
                    self.get_logger().info("get_dashboard_for_emr_serverless_application does not have url")
            except Exception as e:
                self.get_logger().info(f"error in prepare_session: {e}")
                
    def _get_url_from_task_name(self, task_name: str, application_id: str | None):
        if application_id is None:
            raise ValueError("application_id is None")
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
        
