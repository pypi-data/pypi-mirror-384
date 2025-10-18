import abc
import base64
import logging

from IPython import get_ipython
from IPython.core.display import HTML
from IPython.core.display_functions import display

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import Language
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import NoSessionException


class BaseDisplayInterface(metaclass=abc.ABCMeta):
    def __init__(self, display_magic_compute: str, session_manager, s3_path: str) -> None:
        self.display_magic_compute = display_magic_compute
        self.session_manager = session_manager
        self.compute_session_manager = session_manager
        self.s3_path = s3_path

    @abc.abstractmethod
    def get_s3_df_size(self) -> int:
        raise NotImplementedError('Must define get_original_df_size to use this BaseDisplayInterface')

    @abc.abstractmethod
    def upload_dataframe_to_s3(self) -> None:
        raise NotImplementedError('Must define upload_dataframe_to_s3 to use this BaseDisplayInterface')

    def generate_sample_dataframe_str(self) -> str:
        sample_data = self._run_statement(statement=f"""{self.display_magic_compute}.cell_dataframe.to_parquet()""",
                                          mode="eval")
        if isinstance(sample_data, str):
            # Parquet data starts and ends with "PAR1"
            # Slicing is used here to ensure that this is the case and that other characters (like b'' for bytes) are excluded
            parquet_byte_values = sample_data[sample_data.find("PAR1"): sample_data.rfind("PAR1") + 4]
            # This is required for removing the escaped characters and re-encoding the string to the original byte array
            sample_data = parquet_byte_values.encode().decode('unicode_escape').encode('latin-1')
        return base64.b64encode(sample_data).decode('unicode_escape')

    def generate_metadata_str(self) -> str:
        return self._run_statement(statement=f"""{self.display_magic_compute}.get_metadata()""",
                                   mode="eval").replace("\\'", "'")

    def generate_summary_schema_str(self) -> str:
        return self._run_statement(statement=f"""{self.display_magic_compute}.generate_summary_schema()""",
                                   mode="eval").replace("\\'", "'")

    def generate_column_schema_str(self, column: str) -> str:
        return self._run_statement(statement=f"""{self.display_magic_compute}.generate_column_schema(column = "{column}")""",
                                   mode="eval").replace("\\'", "'")

    def generate_echart_data_str(self, x_axis: str, y_axis: str, agg_method: str) -> str:
        return self._run_statement(statement=f"""{self.display_magic_compute}.generate_echart_data(
                                                 x_axis = "{x_axis}",
                                                 y_axis = "{y_axis}",
                                                 agg_method = "{agg_method}")""",
                                   mode="eval").replace("\\'", "'")

    def set_sampling_method(self, sample_method: str, sample_size: int) -> None:
        self._run_statement(statement=f"""{self.display_magic_compute}.set_sampling_method("{sample_method}")
                                           \n{self.display_magic_compute}.set_size({sample_size})
                                           \n{self.display_magic_compute}.sample()""",
                            mode="exec")

    def set_storage(self, storage: str) -> None:
        self._run_statement(statement=f"""{self.display_magic_compute}.set_storage("{storage}")""",
                            mode="exec")

    def get_s3_path(self) -> str:
        return self.s3_path

    def _get_logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(__name__)
        return self._logger

    def _run_statement(self, statement: str, mode="exec") -> str:
        # USE DEFAULT IAM
        if self.compute_session_manager is None:
            if mode == "exec":
                # Executes code on IAM with no return value expected.
                get_ipython().ex(statement)

            elif mode == "eval":
                # Evaluates expression, returning the evaluation
                return get_ipython().ev(statement)
        # USE SESSION MANAGER TO RUN STATEMENT
        else:
            if not self.compute_session_manager.is_session_connectable():
                raise NoSessionException("Session is not connectable")

            try:
                return self.compute_session_manager.run_statement(cell=statement, language=Language.python, mode=mode)
            except NoSessionException as e:
                display(HTML(f"No session exists. "
                             f"Please try to rerun the cell or restart kernel. {e.__class__.__name__}: {e}"))
                self._get_logger().error(f"No session exists.  {e.__class__.__name__}: {e}")
            except Exception as e:
                display(HTML(f"Unable to run statement for connection. {e.__class__.__name__}: {e}"))
                self._get_logger().error(f"Unable to run statement {e.__class__.__name__}: {e}")
