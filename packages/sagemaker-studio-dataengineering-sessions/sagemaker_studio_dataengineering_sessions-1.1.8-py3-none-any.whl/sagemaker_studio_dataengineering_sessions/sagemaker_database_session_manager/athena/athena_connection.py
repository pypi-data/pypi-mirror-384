from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_connection import (
    BaseConnection,
)


class AthenaConnection(BaseConnection):
    def __init__(
        self,
        connection_name: str,
        connection_id: str,
        work_group: str,
        region: str,
        account_id: str,
    ):
        super().__init__(connection_name=connection_name, connection_id=connection_id, region=region)
        self.work_group = work_group
        self.account_id = account_id
