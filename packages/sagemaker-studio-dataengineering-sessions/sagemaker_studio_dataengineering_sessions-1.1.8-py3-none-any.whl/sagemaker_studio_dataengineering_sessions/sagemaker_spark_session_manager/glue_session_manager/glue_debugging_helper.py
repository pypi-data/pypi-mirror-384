import json
import os
from typing import Any, Dict, Optional

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.glue_gateway import GlueGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_connection import GlueConnection
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_debugging_helper import SparkDebuggingHelper


class GlueDebuggingHelper(SparkDebuggingHelper):

    def __init__(self, connection_detail: GlueConnection, gateway: GlueGateway):
        self.connection_detail = connection_detail
        self.glue_gateway = gateway
        
    def get_debugging_info(self, job_id: Optional[str] = None, run_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # TODO: implementation
        return {}

    def write_debugging_info(self, 
                           debugging_info: Dict[str, Any], 
                           output_path: Optional[str] = None,
                           **kwargs) -> bool:
        return True