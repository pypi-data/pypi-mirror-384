import json

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_interface import \
    BaseDisplayInterface


class SparkDisplayInterface(BaseDisplayInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_s3_df_size(self) -> int:
        return self._run_statement(statement=f"""{self.display_magic_compute}.get_s3_df_size()""", mode="eval")

    def upload_dataframe_to_s3(self) -> None:
        self._run_statement(statement=f"""{self.display_magic_compute}.upload_dataframe_to_s3()""", mode="exec")

    def generate_echart_data_str(self, x_axis: str, y_axis: str, agg_method: str) -> str:
        response = self._run_statement(statement=f"""{self.display_magic_compute}.generate_echart_data(
                                                 x_axis = "{x_axis}",
                                                 y_axis = "{y_axis}",
                                                 agg_method = "{agg_method}")""",
                                   mode="eval")
        if isinstance(response, str):
            return response.replace("\\'", "'")
        # When receiving string output from Spark session
        # IPython/Jupyter might automatically convert these strings to Python objects
        # if they look like valid Python literals (e.g., '[["test", "test2"], [1, 2]]' → list)
        return json.dumps(response).replace("\\'", "'")