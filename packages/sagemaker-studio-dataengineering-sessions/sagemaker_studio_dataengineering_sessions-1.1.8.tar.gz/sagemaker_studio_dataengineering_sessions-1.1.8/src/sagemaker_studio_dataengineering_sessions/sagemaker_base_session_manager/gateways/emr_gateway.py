import logging
import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any


 
class EmrGateway():
    def __init__(self, profile=None, region=None, endpoint_url=None):
        self.profile = profile
        self.region = region
        self.endpoint_url = endpoint_url
        self.emr = self._create_emr_client(profile, region, endpoint_url)
        self.logger = logging.getLogger(__name__)
 
    def _create_emr_client(self, profile=None, region=None, endpoint_url=None):
        if not region:
            raise ValueError(f"Region must be set.")
        if profile:
            session = boto3.Session(profile_name=profile)
            return session.client('emr', region_name=region, endpoint_url=endpoint_url)
        else:
            session = boto3.Session()
            return session.client('emr', region_name=region, endpoint_url=endpoint_url)
 
    def get_on_cluster_app_ui_presigned_url(self,
                                            cluster_id: str,
                                            on_cluster_app_ui_type: str,
                                            execution_role_arn: str) -> Dict[str, Any]:
        try:
            result = self.emr.get_persistent_app_ui_presigned_url(ClusterId=cluster_id,
                                                                  OnClusterAppUIType=on_cluster_app_ui_type,
                                                                  executionRoleArn=execution_role_arn)
            return result
        except Exception as e:
            self.logger.error(f"get_on_cluster_app_ui_presigned_url "
                              f"failed for cluster id: {cluster_id}, "
                              f"on_cluster_app_ui_type: {on_cluster_app_ui_type}, "
                              f"execution_role_arn: {execution_role_arn}, because of: {e}")
            raise e

    async def get_on_cluster_app_ui_presigned_url_async(self,
                                                        cluster_id: str,
                                                        on_cluster_app_ui_type: str,
                                                        execution_role_arn: str) -> Dict[str, Any]:
        """
        Async version of get_on_cluster_app_ui_presigned_url using asyncio with ThreadPoolExecutor.
        
        Args:
            cluster_id: The EMR cluster ID
            on_cluster_app_ui_type: The type of on-cluster app UI (e.g., 'Spark', 'Yarn')
            execution_role_arn: The execution role ARN
            
        Returns:
            Dict containing the presigned URL response
            
        Raises:
            Exception: If the AWS API call fails
        """
        loop = asyncio.get_event_loop()
        
        # Run the synchronous boto3 call in a thread pool
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self.get_on_cluster_app_ui_presigned_url,
                cluster_id,
                on_cluster_app_ui_type,
                execution_role_arn
            )
            return result
