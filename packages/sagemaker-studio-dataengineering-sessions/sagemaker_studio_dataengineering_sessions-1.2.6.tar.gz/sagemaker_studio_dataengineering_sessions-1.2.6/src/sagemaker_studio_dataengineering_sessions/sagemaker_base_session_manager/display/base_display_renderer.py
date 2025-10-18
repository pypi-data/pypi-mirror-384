import abc
import json

from IPython import get_ipython
from IPython.core.display_functions import display
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import PROJECT_S3_PATH
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import \
    SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.display.base_display_interface import \
    BaseDisplayInterface

MIME_TYPE = 'application/vnd.sagemaker.display.v2+json'

class BaseDisplayRenderer(metaclass=abc.ABCMeta):
    def __init__(self, display_magic_compute: str, session_manager, storage: str, data_uuid: str, query_result_s3_suffix: str, enable_profiling: bool):
        self.display_magic_compute = display_magic_compute
        self.session_manager = session_manager
        self.storage = storage
        self.data_uuid = data_uuid
        self.s3_path = f"{PROJECT_S3_PATH}/{query_result_s3_suffix}"
        self.interface_id = 'display_interface_' + data_uuid
        self.display_interface = self.create_display_interface()
        self.enable_profiling = enable_profiling
        get_ipython().user_ns[self.interface_id] = self.display_interface

    def render(self) -> None:
        metadata_str = self.display_interface.generate_metadata_str()
        if self.storage == "s3":
            try:
                self.display_interface.upload_dataframe_to_s3()
                if self.enable_profiling:
                    self.display_interface.generate_summary_schema_str()
                display({
                    MIME_TYPE: {
                        'type': "s3",
                        'kernel_id': _get_kernel_id(),
                        'connection_name': self.session_manager.connection_name,
                        'interface_id': self.interface_id,
                        'original_size': self.get_original_size(metadata_str),
                        's3_path': self.s3_path,
                        's3_size': self.display_interface.get_s3_df_size(),
                    }
                }, raw=True)
            except Exception as e:
                SageMakerConnectionDisplay.send_error(e)
        elif self.storage == "cell":
            try:
                display({
                    MIME_TYPE: {
                        'type': "cell",
                        'kernel_id': _get_kernel_id(),
                        'connection_name': self.session_manager.connection_name,
                        'interface_id': self.interface_id,
                        'original_size': self.get_original_size(metadata_str),
                        'data_str': self.display_interface.generate_sample_dataframe_str(),
                        'metadata_str': metadata_str,
                        'summary_schema_str': self.display_interface.generate_summary_schema_str() if self.enable_profiling else "",
                        'column_schema_str_dict': {},
                        'echart_data_str_dict': {}
                    }
                }, raw=True)
            except Exception as e:
                SageMakerConnectionDisplay.send_error(e)

    @abc.abstractmethod
    def create_display_interface(self) -> BaseDisplayInterface:
        pass

    def get_original_size(self, metadata_str: str) -> int:
        metadata = json.loads(metadata_str.encode('utf-8').decode('unicode_escape'))
        return metadata["original_df_size"]


def _get_kernel_id() -> str:
    try:
        return get_ipython().kernel.ident
    except Exception:
        return ""
