from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_interface import \
    BaseDisplayInterface


class IpythonDisplayInterface(BaseDisplayInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Database display uses compute in IPython. Setting compute_session_manager to None
        self.compute_session_manager = None

    def get_s3_df_size(self) -> int:
        return self._run_statement(statement=f"""{self.display_magic_compute}.get_s3_df_size()""", mode="eval")

    def upload_dataframe_to_s3(self) -> None:
        if not self._run_statement(statement=f"""{self.display_magic_compute}.is_dataframe_existing()""", mode="eval"):
            self._run_statement(statement=f"""{self.display_magic_compute}.upload_dataframe_to_s3()""", mode="exec")
