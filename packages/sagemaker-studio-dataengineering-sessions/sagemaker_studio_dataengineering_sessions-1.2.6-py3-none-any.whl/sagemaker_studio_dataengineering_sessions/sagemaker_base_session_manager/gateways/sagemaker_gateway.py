import logging
from typing import Dict, Any, Optional


class SageMakerGateway:
    
    def __init__(self, sagemaker_client):
        self.sagemaker_client = sagemaker_client
        self.logger = logging.getLogger(__name__)
    
    def describe_space(self, domain_id: str, space_name: str) -> Dict[str, Any]:
        """
        Call the SageMaker describe-space API to get information about a SageMaker Studio space.
        
        Args:
            domain_id (str): The ID of the domain that contains the space.
            space_name (str): The name of the space to describe.
            
        Returns:
            Dict[str, Any]: The response from the describe-space API call.
            
        Raises:
            Exception: If there's an error retrieving the space information.
        """
        self.logger.info(f"Describing SageMaker Studio space: {space_name} in domain: {domain_id}")
        try:
            response = self.sagemaker_client.describe_space(
                DomainId=domain_id,
                SpaceName=space_name
            )
            return response
        except Exception as e:
            self.logger.error(f"Error describing SageMaker Studio space {space_name} in domain {domain_id}: {str(e)}")
            raise
