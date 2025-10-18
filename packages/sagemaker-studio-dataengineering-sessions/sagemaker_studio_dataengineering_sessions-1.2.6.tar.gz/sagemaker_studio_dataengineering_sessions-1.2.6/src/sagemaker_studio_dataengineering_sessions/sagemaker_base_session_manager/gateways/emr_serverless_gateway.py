import logging
import boto3

class EmrServerlessGateway():
    def __init__(self, profile: str | None = None, region: str | None = None):
        self.initialize_clients(profile, region)

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
    
    def get_dashboard_for_emr_serverless_application(self, application_id: str, job_run_id: str):
        response = self.emr_serverless_client.get_dashboard_for_job_run(
            applicationId=application_id,
            jobRunId=job_run_id,
            accessSystemProfileLogs=False)
        return response
