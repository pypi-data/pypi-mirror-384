from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_renderer import \
    BaseDisplayRenderer

from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.display.spark_display_interface import \
    SparkDisplayInterface


class SparkDisplayRenderer(BaseDisplayRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_display_interface(self):
        return SparkDisplayInterface(display_magic_compute=self.display_magic_compute,
                                     session_manager=self.session_manager,
                                     s3_path=self.s3_path)
