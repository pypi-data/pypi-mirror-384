from typing import Any, Dict, Optional

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_gateway import EmrGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_connection import EmrOnEc2Connection


class EmrOnEc2DebuggingHelper(BaseDebuggingHelper):
    def __init__(self, connection_detail: EmrOnEc2Connection, gateway: EmrGateway):
        self.connection_detail = connection_detail
        self.emr_gateway = gateway
        
    def get_debugging_info(self, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # TODO: implementation
        return {}

    def write_debugging_info(self, 
                           debugging_info: Dict[str, Any], 
                           cell_id: str,
                           **kwargs) -> bool:
        # TODO: implementation
        return True