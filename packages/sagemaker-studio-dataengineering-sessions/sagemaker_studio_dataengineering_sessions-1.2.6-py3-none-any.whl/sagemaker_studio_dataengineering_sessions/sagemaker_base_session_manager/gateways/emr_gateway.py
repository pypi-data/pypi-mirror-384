import logging
import boto3
import asyncio
from typing import Dict, Any, Coroutine


 
class EmrGateway():
    """
    EmrGateway class to abstract the boto3 emr client
    """
    logger = logging.getLogger(__name__)
    def __init__(self, emr):
        self.emr = emr
 
    def get_on_cluster_app_ui_presigned_url(self,
                                            cluster_id: str,
                                            on_cluster_app_ui_type: str,
                                            execution_role_arn: str) -> Dict[str, Any]:
        self.logger.info(f"get_on_cluster_app_ui_presigned_url with cluster id:{cluster_id}, "
                         f"on_cluster_app_ui_type: {on_cluster_app_ui_type}, execution_role_arn: {execution_role_arn}")
        try:
            self.logger.info(f"calling get_on_cluster_app_ui_presigned_url with cluster id:{cluster_id}, " 
                             f"on_cluster_app_ui_type: {on_cluster_app_ui_type}, execution_role_arn: {execution_role_arn}")
            result = self.emr.get_on_cluster_app_ui_presigned_url(ClusterId=cluster_id,
                                                                  OnClusterAppUIType=on_cluster_app_ui_type,
                                                                  ExecutionRoleArn=execution_role_arn)
            self.logger.info(result)
            return result
        except Exception as e:
            self.logger.error(f"get_on_cluster_app_ui_presigned_url "
                              f"failed for cluster id: {cluster_id}, "
                              f"on_cluster_app_ui_type: {on_cluster_app_ui_type}, "
                              f"execution_role_arn: {execution_role_arn}, because of: {e}")
            raise e
