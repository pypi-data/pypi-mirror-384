import logging
import boto3

class EmrServerlessGateway():
    def __init__(self):
        self.emr_serverless_client = None

    def initialize_clients(self, profile=None, region=None):
        self.emr_serverless_client = self.create_emr_serverless_client(profile, region)
        self.logger = logging.getLogger(__name__)


    def create_emr_serverless_client(self, profile=None, region=None):
        if not region:
            raise ValueError(f"Region must be set.")
        if profile:
            return boto3.Session(profile_name=profile).client(
                "emr-serverless", region_name=region
            )
        else:
            return boto3.Session().client(
                "emr-serverless",
                region_name=region)

    def get_emr_serverless_application_state(self, applicationId: str):
        response = self.emr_serverless_client.get_application(applicationId=applicationId)
        return response['application']['state']

    def get_emr_serverless_application(self, applicationId: str):
        response = self.emr_serverless_client.get_application(applicationId=applicationId)
        return response['application']

    def start_emr_serverless_application(self, applicationId: str):
        self.emr_serverless_client.start_application(applicationId=applicationId)
        return

    def stop_emr_serverless_application(self, applicationId: str):
        self.emr_serverless_client.stop_application(applicationId=applicationId)
        return

