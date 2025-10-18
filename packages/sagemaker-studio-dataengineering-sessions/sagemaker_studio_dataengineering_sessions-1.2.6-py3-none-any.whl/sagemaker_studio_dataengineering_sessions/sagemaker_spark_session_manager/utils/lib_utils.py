import json

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import LIB_PATH


def _read_libs(config_path):
    # Opening JSON file
    try:
        with open(config_path) as f:
            data = json.load(f)
            f.close()
            return data
    except Exception:
        # FileNotFoundError or JsonParseError should not fail the magic initialization
        return {}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LibProvider(metaclass=Singleton):
    __maven_artifacts = []
    __pypi_modules = []
    __conda_modules = []
    __s3_python_libs = []
    __s3_java_libs = []
    __local_python_libs = []
    __local_java_libs = []
    __other_python_libs = []
    __other_java_libs = []
    __archive = ""

    def __init__(self):
        self.refresh()

    def refresh(self):
        data = _read_libs(LIB_PATH)

        if data:
            # The name should match the schema in SageMakerConnectionMagicsJLExtension
            if "Jar" in data:
                jar_data = data["Jar"]
                if "MavenArtifacts" in jar_data:
                    self.__maven_artifacts = jar_data["MavenArtifacts"]
                if "S3Paths" in jar_data:
                    self.__s3_java_libs = jar_data["S3Paths"]
                if "LocalPaths" in jar_data:
                    self.__local_java_libs = jar_data["LocalPaths"]
                if "OtherPaths" in jar_data:
                    self.__other_java_libs = jar_data["OtherPaths"]
            if "Python" in data:
                python_data = data["Python"]
                if "PyPIPackages" in python_data:
                    self.__pypi_modules = python_data["PyPIPackages"]
                if "CondaPackages" in python_data:
                    self.__conda_modules = python_data["CondaPackages"]
                if "S3Paths" in python_data:
                    self.__s3_python_libs = python_data["S3Paths"]
                if "LocalPaths" in python_data:
                    self.__local_python_libs = python_data["LocalPaths"]
                if "OtherPaths" in python_data:
                    self.__other_python_libs = python_data["OtherPaths"]
                # if "ArchivePath" in python_data:
                    # self.__archive = python_data["ArchivePath"]

    def get_maven_artifacts(self) -> dict:
        return self.__maven_artifacts.copy()

    def get_pypi_modules(self) -> dict:
        return self.__pypi_modules.copy()

    def get_conda_modules(self) -> dict:
        return self.__conda_modules.copy()

    def get_s3_python_libs(self) -> dict:
        return self.__s3_python_libs.copy()

    def get_s3_java_libs(self) -> dict:
        return self.__s3_java_libs.copy()

    def get_local_python_libs(self) -> dict:
        return self.__local_python_libs.copy()

    def get_local_java_libs(self) -> dict:
        return self.__local_java_libs.copy()

    def get_other_python_libs(self) -> dict:
        return self.__other_python_libs.copy()

    def get_other_java_libs(self) -> dict:
        return self.__other_java_libs.copy()

    def get_archive(self) -> str:
        return self.__archive
