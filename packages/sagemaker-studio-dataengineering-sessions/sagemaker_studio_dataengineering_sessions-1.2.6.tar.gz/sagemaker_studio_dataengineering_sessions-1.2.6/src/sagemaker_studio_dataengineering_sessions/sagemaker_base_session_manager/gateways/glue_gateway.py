import boto3
import os
import logging

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DATAZONE_DOMAIN_REGION


class GlueGateway:
    def __init__(self, glue_client):
        self.glue_client = glue_client
        self.logger = logging.getLogger(__name__)
        
    def get_dashboard_url(self, resource_id: str, resource_type: str):
        """
        Get the dashboard URL for a Glue resource.
        
        Args:
            resource_id (str): The ID of the resource.
            resource_type (str): The type of the resource.
            
        Returns:
            str: The dashboard URL or None if not available.
        """
        response = self.glue_client.get_dashboard_url(ResourceId=resource_id, ResourceType=resource_type).get('Url', None)
        return response
        
    def get_interactive_session(self, session_id: str):
        """
        Get the details of an interactive Glue session.
        
        Args:
            session_id (str): The ID of the Glue interactive session to check.
            
        Returns:
            dict: The session details containing information such as status, creation time, etc.
            
        Raises:
            Exception: If there's an error retrieving the session information.
        """
        self.logger.info(f"Getting details for Glue interactive session: {session_id}")
        try:
            response = self.glue_client.get_session(Id=session_id)
            session = response.get('Session', {})
            return session
        except Exception as e:
            self.logger.error(f"Error retrieving details for session {session_id}: {str(e)}")
            raise

    def get_catalogs(self, parent_catalog_id=None):
        self.logger.info(f"get_catalogs start. parent_catalog_id = {parent_catalog_id}")
        next_token = None
        catalogs = []
        while True:
            if next_token:
                response = self.glue_client.get_catalogs(Recursive=True, HasDatabases=True, NextToken=next_token)
            else:
                response = self.glue_client.get_catalogs(Recursive=True, HasDatabases=True)
            catalogs.extend(response['CatalogList'])
            if not 'NextToken' in response:
                break
            else:
                next_token = response['NextToken']
        self.logger.info("get_catalogs done.")
        return catalogs
