import boto3
import botocore
import os
import logging

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import DOMAIN_ID, PROJECT_ID, DATAZONE_ENDPOINT_URL, \
    DATAZONE_DOMAIN_REGION


class DataZoneGateway:
    def __init__(self):
        self.datazone_client = None
        self.logger = logging.getLogger(__name__)
        self.domain_identifier = None
        self.project_identifier = None
        self._clients_initialized = False

    def initialize_default_clients(self):
        if self._clients_initialized:
            self.logger.debug("Default clients already initialized, skipping.")
            return
    
        self.initialize_clients(profile="default",
                                region=DATAZONE_DOMAIN_REGION,
                                endpoint_url=DATAZONE_ENDPOINT_URL,
                                domain_identifier=DOMAIN_ID,
                                project_identifier=PROJECT_ID)
        self._clients_initialized = True

    def initialize_clients(self, profile=None, region=None, endpoint_url=None, domain_identifier=None, project_identifier=None):
        if domain_identifier is None:
            raise RuntimeError("Domain identifier must be provided")
        self.domain_identifier = domain_identifier
        self.project_identifier = project_identifier
        self.datazone_client = self._create_datazone_client(profile, region, endpoint_url)
        self._clients_initialized = True

    def list_connections(self, project_id=None):
        if self.datazone_client is None:
            self.initialize_default_clients()
        next_token = None
        project_identifier = project_id if project_id else self.project_identifier
        connections = []
        while True:
            try:
                if next_token:
                    response = self.datazone_client.list_connections(domainIdentifier=self.domain_identifier,
                                                                     projectIdentifier=project_identifier,
                                                                     nextToken=next_token)
                else:
                    response = self.datazone_client.list_connections(domainIdentifier=self.domain_identifier,
                                                                     projectIdentifier=project_identifier)
                connections.extend(response['items'])
                if not 'nextToken' in response:
                    break
                else:
                    next_token = response['nextToken']
            except botocore.exceptions.ClientError as err:
                self.logger.error(f"Could not list connections."
                                  f"Request ID: {err.response['ResponseMetadata']['RequestId']}. "
                                  f"Http code: {err.response['ResponseMetadata']['HTTPStatusCode']}")
                raise err
        return connections

    def get_connection(self, connection_id, with_secret=False):
        if self.datazone_client is None:
            self.initialize_default_clients()
        try:
            connection = self.datazone_client.get_connection(domainIdentifier=self.domain_identifier,
                                                             identifier=connection_id,
                                                             withSecret=with_secret)
            return connection
        except botocore.exceptions.ClientError as err:
            self.logger.error(f"Could not get_connection for connection id: {connection_id}. "
                              f"Request ID: {err.response['ResponseMetadata']['RequestId']}. "
                              f"Http code: {err.response['ResponseMetadata']['HTTPStatusCode']}")
            raise err

    def get_domain(self):
        if self.domain_identifier is None:
            return None
            
        if self.datazone_client is None:
            self.initialize_default_clients()

        try:
            domain = self.datazone_client.get_domain(identifier=self.domain_identifier)
            return domain
        except botocore.exceptions.ClientError as err:
            self.logger.error(f"Could not get_domain for domain id: {self.domain_identifier}. "
                              f"Request ID: {err.response['ResponseMetadata']['RequestId']}. "
                              f"Http code: {err.response['ResponseMetadata']['HTTPStatusCode']}")
            raise err

    def _get_aws_model_dir(self):
        # TODO: remove until aws model is public
        try:
            import sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager
            path = os.path.dirname(sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.__file__)
            return path + "/boto3_models"
        except ImportError:
            raise RuntimeError("Unable to import sagemaker_base_session_manager, "
                               "thus cannot initialize datazone client.")


    def get_username(self, user_id):
        if self.datazone_client is None:
            self.initialize_default_clients()
            
        try:
            response = self.datazone_client.get_user_profile(
                domainIdentifier=self.domain_identifier,
                userIdentifier=user_id
            )
            auth_type = response['type']
            if auth_type == 'IAM':
                arn = response['details']['iam']['arn']
                username = arn.split('/')[-1]
                return username
            elif auth_type in ['SSO', 'SAML']:
                username = response['details']['sso']['username']
                return username
            else:
                raise ValueError(f"Unsupported authentication type: {auth_type}")
        except botocore.exceptions.ClientError as err:
            self.logger.error(f"Failed to get user profile: {err}")
            raise err
        except Exception as e:
            raise e

    def get_project_tooling_environment(self, project_id=None):
        if self.datazone_client is None:
            self.initialize_default_clients()
            
        try:
            blueprint_response = self.datazone_client.list_environment_blueprints(
                domainIdentifier=self.domain_identifier,
                name="Tooling",
                managed=True,
                provider="Amazon SageMaker"
            )

            if not blueprint_response.get('items'):
                self.logger.error("DataZone-Tooling environment blueprint not found")
                return None
            blueprint = blueprint_response['items'][0]

            project_identifier = project_id if project_id else self.project_identifier
            environments_response = self.datazone_client.list_environments(
                domainIdentifier=self.domain_identifier,
                projectIdentifier=project_identifier,
                environmentBlueprintIdentifier=blueprint['id'],
                provider="Amazon SageMaker"
            )

            if not environments_response.get('items'):
                self.logger.error("No environments found")
                return None

            environments = environments_response['items']
            default_env = sorted(environments, key=lambda x: x.get('deploymentOrder', float('inf')))[0]
            return default_env
        except Exception as e:
            self.logger.error(f"Failed to get tooling environment: {str(e)}")
            return None

    def is_s3_ag_enabled_for_environment(self, environment):
        if not environment or not environment.get('provisionedResources'):
            return False
        s3_ag_resources = [
            resource for resource in environment['provisionedResources']
            if resource.get('name') == 'enableS3AccessGrantsForTools'
        ]
        if s3_ag_resources:
            value = s3_ag_resources[0].get('value', '')
        else:
            self.logger.error("enableS3AccessGrantsForTools not found in provisioned resources")
        return bool(s3_ag_resources and s3_ag_resources[0].get('value', '').lower() == 'true')
    
    def is_express_mode(self, domain = None) -> bool:
        if not domain or not domain.get('preferences') or not domain.get('preferences').get("DOMAIN_MODE"):
            return False
        return bool(domain.get('preferences').get("DOMAIN_MODE") == "EXPRESS")
    
    def _create_datazone_client(self, profile=None, region=None, endpoint_url=None):
        # add the private model of datazone
        os.environ['AWS_DATA_PATH'] = self._get_aws_model_dir()
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        if endpoint_url:
            return session.client("datazone", region_name=region, endpoint_url=endpoint_url)
        else:
            return session.client("datazone", region_name=region)
