from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_connection import (
    BaseConnection,
)


class RedshiftConnection(BaseConnection):
    def __init__(
        self,
        connection_name: str,
        connection_id: str,
        host: str,
        database: str,
        port: str,
        auth_type: str,
        secret_arn: str,
        region: str,
        account_id: str,
        enable_tip: bool = False,
    ):
        super().__init__(
            connection_name=connection_name, connection_id=connection_id, region=region, enable_tip=enable_tip
        )
        self.host = host
        self.database = database
        self.port = port
        self.auth_type = auth_type
        self.secret_arn = secret_arn
        self.account_id = account_id
