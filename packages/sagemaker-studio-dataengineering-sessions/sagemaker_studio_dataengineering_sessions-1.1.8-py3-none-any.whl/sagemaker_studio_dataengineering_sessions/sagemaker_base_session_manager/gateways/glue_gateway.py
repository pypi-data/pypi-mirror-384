import boto3
import os
import logging

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DATAZONE_DOMAIN_REGION


class GlueGateway:
    def __init__(self, glue_client):
        self.glue_client = glue_client
        self.logger = logging.getLogger(__name__)

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

