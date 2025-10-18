"""
EMR on Serverless debugging helper for SageMaker Studio Data Engineering Sessions.

This module provides debugging capabilities specific to EMR on Serverless sessions.
"""

import json
import os
from typing import Any, Dict, Optional

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.emr_serverless_gateway import EmrServerlessGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_connection import EmrOnServerlessConnection



class EmrOnServerlessDebuggingHelper(BaseDebuggingHelper):
    """
    Debugging helper implementation for EMR on Serverless sessions.
    
    Provides methods to retrieve and write debugging information
    specific to EMR on Serverless applications.
    """

    def __init__(self, connection_detail: EmrOnServerlessConnection, gateway: EmrServerlessGateway):
        self.connection_detail = connection_detail
        self.EmrServerlessGateway = gateway
        
    def get_debugging_info(self, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # TODO: impelemtation
        return {}

    def write_debugging_info(self, 
                           debugging_info: Dict[str, Any], 
                           cell_id: str,
                           **kwargs) -> bool:
        # TODO: implementation
        return True