import sys

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.spark_display_compute import \
    SparkDisplayCompute
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.s3_manager.s3_variable_manager import \
    S3VariableManager


class IpythonDisplayCompute(SparkDisplayCompute):
    def __init__(
        self,
        df,
        last_line_execution=False,
        size=10000,
        sampling_method="head",
        columns=None,
        type_inference=False,
        plot_lib="default",
        spark_use_threshold=1_000_000,
        max_sample=1_000_000_000,
        graph_render_threshold=1_000_000,
        storage="cell",
        project_s3_path=None,
        query_result_s3_suffix=None,
        **kwargs
    ):
        self.df = df
        self.last_line_execution = last_line_execution
        self.valid_df_type = False
        self.size = size
        self.sampling_method = sampling_method
        self.columns = columns
        self.type_inference = type_inference
        self.plot_lib = plot_lib

        self.spark_use_threshold = spark_use_threshold
        self.max_sample = max_sample
        self.graph_render_threshold = graph_render_threshold
        self.storage = storage
        self.project_s3_path = project_s3_path
        self.query_result_s3_suffix = query_result_s3_suffix
        self.s3_handler = S3VariableManager(project_s3_path=project_s3_path)

        try:
            self.spark = None
            self.compute_validation()
            self.valid_df_type = True
        except Exception as e:
            self.valid_df_type = False
            # If this object is being created for the last line of a cell (which is not a %display call), validation must fail silently
            # This can happen when the last evaluates to a type that is not a dataframe
            if not self.last_line_execution:
                raise ValueError("Validation failed for creating rich display compute module.") from e
            else:
                sys.stdout.write(f"Validation failed for creating rich display compute module. Error: {e} \n")
                sys.stdout.flush()

        self._process_df()

    # Samples the dataframe passed in.
    def sample(self, size=None):
        size = self.size if size is None else size
        df_type = self.get_dataframe_type(self.df)

        if self.columns is not None:
            if df_type in ["pandas", "pandas-on-spark"]:
                self.df = self.df.loc[:, self.columns]
        if (df_type == "pandas"):
            return self.sample_pandas(self.df, size, self.sampling_method)
        else:
            raise TypeError(f"Invalid Dataframe Type: {type(self.df)}")

    def upload_dataframe_to_s3(self):
        if self.storage == "s3":
            self.s3_handler.upload_parquet(self.df, f"{self.query_result_s3_suffix}dataframe/dataframe.parquet")

    def is_dataframe_existing(self):
        return self.s3_handler.check_folder_exists(f"{self.query_result_s3_suffix}dataframe/")
