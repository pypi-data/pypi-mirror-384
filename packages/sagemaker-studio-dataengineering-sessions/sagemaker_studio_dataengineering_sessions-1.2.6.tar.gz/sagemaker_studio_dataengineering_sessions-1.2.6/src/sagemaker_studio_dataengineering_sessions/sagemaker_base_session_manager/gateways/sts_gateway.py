import boto3
import logging

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DATAZONE_DOMAIN_REGION
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.cache import ttl_cache


class StsGateway:
    def __init__(self, sts_client):
        self.sts_client = sts_client
        self.logger = logging.getLogger(__name__)

    @ttl_cache(ttl_seconds=3600)
    def get_source_identity(self):
        try:
            response = self.sts_client.get_caller_identity()
            return response['Arn'].split('/')[-1].split('@')[0]
        except Exception as e:
            self.logger.error("Failed to retrieve source identity.", e)
            raise e
