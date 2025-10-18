from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_connection import BaseConnection


class SparkConnection(BaseConnection):
    def __init__(self, connection_name: str,
                 connection_id: str,
                 region: str,
                 spark_configs: dict[str, any] | None = None):
        super().__init__(connection_name=connection_name,
                         connection_id=connection_id,
                         region=region)
        self.spark_configs = spark_configs
