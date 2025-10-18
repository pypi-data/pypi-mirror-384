from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.governance_type import GovernanceType
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_connection import \
    SparkConnection


class EmrOnEc2Connection(SparkConnection):
    def __init__(self,
                 connection_name: str,
                 connection_id: str,
                 cluster_id: str,
                 runtime_role_arn: str,
                 trusted_certificates_s3_uri: str,
                 url: str,
                 governance_type: GovernanceType,
                 region: str,
                 spark_configs: dict[str, any] | None = None):
        super().__init__(connection_name=connection_name,
                         connection_id=connection_id,
                         region=region,
                         spark_configs=spark_configs)
        self.cluster_id = cluster_id
        self.runtime_role_arn = runtime_role_arn
        self.trusted_certificates_s3_uri = trusted_certificates_s3_uri
        self.url = url
        self.governance_type = governance_type
