from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_renderer import \
    BaseDisplayRenderer
from sagemaker_studio_dataengineering_sessions.sagemaker_ipython_session_manager.display.ipython_display_interface \
    import IpythonDisplayInterface


class IpythonDisplayRenderer(BaseDisplayRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_display_interface(self):
        return IpythonDisplayInterface(display_magic_compute=self.display_magic_compute,
                                       session_manager=self.session_manager,
                                       s3_path=self.s3_path)
