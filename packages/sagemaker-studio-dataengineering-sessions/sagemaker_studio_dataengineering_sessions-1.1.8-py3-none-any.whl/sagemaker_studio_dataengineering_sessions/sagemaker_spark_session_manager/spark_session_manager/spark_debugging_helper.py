"""
Spark debugging helper for SageMaker Studio Data Engineering Sessions.

This module provides debugging capabilities specific to Spark sessions.
"""

import abc
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper


class SparkDebuggingHelper(BaseDebuggingHelper, metaclass=abc.ABCMeta):

    def get_spark_configurations(self):
        # TODO: implementation
        pass

    def get_failed_tasks(self):
        # TODO: implementation
        pass



