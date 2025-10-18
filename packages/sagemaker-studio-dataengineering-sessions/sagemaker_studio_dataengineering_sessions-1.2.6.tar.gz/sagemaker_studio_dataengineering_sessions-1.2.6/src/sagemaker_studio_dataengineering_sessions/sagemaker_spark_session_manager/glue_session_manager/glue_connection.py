from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_connection import \
    SparkConnection


class GlueConnection(SparkConnection, object):
    def __init__(self, connection_name: str,
                 connection_id: str,
                 region: str,
                 account: str,
                 project: str,
                 glue_connection: str,
                 glue_iam_role: str,
                 session_configs: dict[str, any],
                 default_arguments: dict[str, any] | None = None,
                 spark_configs: dict[str, any] | None = None,
                 related_redshift_properties: dict[str, any] | None = None):
        super().__init__(connection_name=connection_name,
                         connection_id=connection_id,
                         region=region,
                         spark_configs=spark_configs)
        self.account = account
        self.project = project
        self.glue_connection = glue_connection
        self.glue_iam_role = glue_iam_role
        self.session_configs = session_configs
        self.related_redshift_properties = related_redshift_properties
        self.default_arguments = default_arguments
