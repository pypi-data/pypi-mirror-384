import logging
import time
from typing import Any, Dict, Optional, TYPE_CHECKING

import requests

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.logger_utils import setup_logger
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_gateway import EmrGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_debugging_helper import GET_RESOURCE_MANAGER_YARN_DIAGNOSTIC, GET_SPARK_ALL_EXECUTORS, GET_SPARK_CONFIGURATIONS, GET_SPARK_FAILED_JOBS, GET_SPARK_FAILED_TASKS_DETAILS, GET_SPARK_UNKNOWN_JOBS, SparkDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_session import SparkSession

if TYPE_CHECKING:
    from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_session import EmrOnEc2Session

SPARK_HISTORY_SERVER_ON_CLUSTER_APP_UI_TYPE = "SparkHistoryServer"
logger = logging.getLogger(__name__)


class EmrOnEc2DebuggingHelper(SparkDebuggingHelper):
    
    def __init__(self, gateway: EmrGateway, session: "EmrOnEc2Session"):
        super().__init__()
        self.gateway = gateway
        self.session = session


    def prepare_session(self, **kwargs) -> None:
        logger.info(f"prepare for session - cluster id: {self.session.connection_details.cluster_id},  ExecutionRoleArn: {self.session.connection_details.runtime_role_arn}")
        self.get_logger().info(f"prepare for session - cluster id: {self.session.connection_details.cluster_id},  ExecutionRoleArn: {self.session.connection_details.runtime_role_arn}")

        try:
            get_on_cluster_app_ui_response = self.gateway.get_on_cluster_app_ui_presigned_url(
                cluster_id=self.session.connection_details.cluster_id, 
                on_cluster_app_ui_type=SPARK_HISTORY_SERVER_ON_CLUSTER_APP_UI_TYPE, 
                execution_role_arn=self.session.connection_details.runtime_role_arn)
            self.get_logger().info(get_on_cluster_app_ui_response)
            presigned_url = get_on_cluster_app_ui_response["PresignedURL"]
            if presigned_url:
                self.clean_up_request_session()
                self.request_session = requests.Session()
                response = self.request_session.get(presigned_url, allow_redirects=True)
                self.spark_ui_base_url = response.url.rsplit("?", 1)[0]
                self.yarn_resource_manager_base_url = self.spark_ui_base_url.replace("shs", "rm")
            else:
                self.get_logger().info("get_on_cluster_app_ui_response does not have PresignedURL")
        except Exception as e:
            self.get_logger().info(f"error in prepare_session: {e}")
        
    def _get_url_from_task_name(self, task_name: str, application_id: str | None):
        if application_id is None:
            raise ValueError("application_id is None")
        if task_name == GET_SPARK_UNKNOWN_JOBS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/1/jobs?status=unknown"
        elif task_name == GET_SPARK_FAILED_JOBS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/1/jobs?status=failed"
        elif task_name == GET_SPARK_FAILED_TASKS_DETAILS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/1/stages/?details=true&taskStatus=FAILED&?withSummaries=true"
        elif task_name == GET_SPARK_ALL_EXECUTORS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/1/allexecutors/"
        elif task_name == GET_SPARK_CONFIGURATIONS:
            target_url = f"{self.spark_ui_base_url}api/v1/applications/{application_id}/1/environment/"
        elif task_name == GET_RESOURCE_MANAGER_YARN_DIAGNOSTIC:
            target_url = f"{self.yarn_resource_manager_base_url}ws/v1/cluster/apps/{application_id}"
        else:
            raise ValueError(f"Unknown task name: {task_name}")
        return target_url

    

