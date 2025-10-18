import abc
import json
import logging
import uuid

import pandas
from IPython.core.error import UsageError
from IPython.core.getipython import get_ipython
from IPython.core.display import Javascript

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_debugging_helper import BaseDebuggingHelper
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_session_manager import \
    BaseSessionManager
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import Language, \
    DATAZONE_STAGE, PROJECT_S3_PATH, USER_ID, DATAZONE_DOMAIN_REGION, DATAZONE_ENDPOINT_URL, DOMAIN_ID, PROJECT_ID, \
    METADATA_CONTENT, IS_REMOTE_WORKFLOW, USER_ID
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.debugging_utils import \
    get_cell_id, get_cell_content
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.glue_gateway import GlueGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.datazone_gateway import DataZoneGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import \
    SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_commands.send_to_spark_command import \
    send_dict_to_spark_command, \
    send_str_to_spark_command, send_pandas_df_to_spark_command, send_datazone_metadata_command
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.common_utils import \
    get_account_id_from_arn, get_glue_endpoint, get_redshift_endpoint
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.utils.lib_utils import LibProvider
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import \
    SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_connection import \
    SparkConnection
from IPython.display import display
import ipywidgets as widgets
from botocore.exceptions import ClientError

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    CONNECTION_TYPE_SPARK_GLUE, CONNECTION_TYPE_SPARK_EMR_SERVERLESS
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import \
    ExecutionException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.client_utils import create_glue_client
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.display.spark_display_renderer import \
    SparkDisplayRenderer


class SparkSession(BaseSessionManager, metaclass=abc.ABCMeta):
    # Do not change this without updating the SageMakerDebuggingJLPlugin
    CREATE_SESSION_MSG = "Create session for connection: {}"
    INFO_TABLE_MSG = "Session information table for connection: {}"

    lib_provider = LibProvider()
    logger = logging.getLogger(__name__)

    def __init__(self, connection_name):
        super().__init__()
        self.iceberg_enabled = True
        self.auto_add_catalogs = True
        self.connection_name = connection_name
        aws_location = self._get_connection_aws_location()
        self.region = aws_location["awsRegion"]
        self.account_id = aws_location["awsAccountId"]
        self.glue_endpoint = get_glue_endpoint(self.region, DATAZONE_STAGE)
        self.redshift_endpoint = get_redshift_endpoint(self.region, DATAZONE_STAGE)
        self.glue_client = create_glue_client(self.profile, self.region)
        self.glue_gateway = GlueGateway(self.glue_client)
        self.datazone_gateway = DataZoneGateway()
        self.datazone_gateway.initialize_default_clients()
        self.s3_variable_manager_name = None

    def send_to_remote(self, local_var: str, remote_var: str, language=Language.python):
        try:
            local = get_ipython().ev(f"{local_var}")
            if type(local) is dict:
                command = send_dict_to_spark_command(local, remote_var, language)
            elif type(local) is str:
                command = send_str_to_spark_command(local, remote_var, language)
            elif type(local) is pandas.DataFrame:
                command = send_pandas_df_to_spark_command(local, remote_var, language)
            else:
                raise NotImplementedError(f"Local variable {type(local)} is not supported.")
            if not self.is_session_connectable():
                self.create_session()
            self.run_statement(cell=command, language=language)
        except NameError:
            self.get_logger().error(f"local variable  does not exist.")
            raise RuntimeError(f"local variable {local_var} does not exist.")

    def send_datazone_metadata_to_remote(self, language=Language.python):
        if language == Language.python:
            # Only send metadata if language is python
            command = send_datazone_metadata_command(language)
            self.run_statement(cell=command, language=language, interactive_debugging=False)

    def _create_display_renderer(self, **kwargs):
        try:
            display_compute_id = kwargs.get('display_compute_id')
            create_compute = self.run_statement(
                language=Language.python,
                cell=f"""{display_compute_id} = SparkDisplayCompute(df={kwargs.get('df')},
                 size={kwargs.get('size')},
                 last_line_execution={kwargs.get('last_line_execution')},
                 sampling_method="{kwargs.get('sampling_method')}",
                 spark_session={kwargs.get('spark_session')},
                 columns={kwargs.get('columns')},
                 type_inference={kwargs.get('type_inference')},
                 plot_lib="{kwargs.get('plot_lib')}",
                 spark_use_threshold={kwargs.get('spark_use_threshold')},
                 max_sample={kwargs.get('max_sample')},
                 graph_render_threshold={kwargs.get('graph_render_threshold')},
                 storage="{kwargs.get('storage') or "cell"}",
                 project_s3_path="{PROJECT_S3_PATH}",
                 query_result_s3_suffix="{kwargs.get('query_result_s3_suffix')}")""",
            )
            # Return None, do not try to create a renderer object as it will fail if the DisplayMagicCompute creation fails
            if create_compute != "" and create_compute is not None:  # create compute also stores any warnings
                self.logger.warning(f"Warnings from display compute creation: {create_compute}")
                return None
            return SparkDisplayRenderer(session_manager=self,
                                        data_uuid=kwargs.get('display_uuid'),
                                        display_magic_compute=display_compute_id,
                                        storage=kwargs.get('storage'),
                                        query_result_s3_suffix=kwargs.get('query_result_s3_suffix'),
                                        enable_profiling=kwargs.get('enable_profiling'))
        except Exception as e:
            self.get_logger().error(f"Could not create display compute: {e}")
            return None

    def _configure_core(self, cell):
        raise NotImplementedError('Must define _configure_core to use this configure function.')

    def _get_connection_aws_location(self):
        connection_details = SageMakerToolkitUtils.get_connection_detail(self.connection_name, True)
        return connection_details["physicalEndpoints"][0]["awsLocation"]

    def _gen_default_spark_configuration(self):
        if not self.iceberg_enabled:
            # Do not add Glue catalog configuration if Iceberg is not enabled
            self.default_spark_configuration = {}
            return

        self.default_spark_configuration = {
            "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
            "spark.sql.catalog.spark_catalog.catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
            "spark.sql.catalog.spark_catalog.glue.id": self.account_id,
            "spark.sql.catalog.spark_catalog.glue.account-id": self.account_id,
            "spark.sql.catalog.spark_catalog.client.region": self.region,
            "spark.sql.catalog.spark_catalog.glue.endpoint": get_glue_endpoint(self.region),

            "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            "spark.datasource.redshift.community.glue_endpoint": self.glue_endpoint,
            "spark.datasource.redshift.community.data_api_endpoint": self.redshift_endpoint,
            "spark.hadoop.fs.s3.impl": "com.amazon.ws.emr.hadoop.fs.EmrFileSystem"
        }
        if self.auto_add_catalogs:
            self._gen_catalog_config()
        self.logger.info(f"update default configuration: {self.default_spark_configuration}")

    def _is_fta_supported(self):
        return False

    def _gen_catalog_config(self):
        try:
            catalogs = self.glue_gateway.get_catalogs()
            conf = self.default_spark_configuration
            for catalog in catalogs:
                if (catalog['CatalogType'] == "FEDERATED"
                    and catalog['FederatedCatalog']['ConnectionName'] != "aws:s3tables"):
                    pass
                else:
                    # Confirmed with glue team. If a catalog hierarchy looks like level_1 -> level_2 -> level_3 -> dev
                    # The ParentCatalogNames list of catalog dev would be
                    # index 0: level_1
                    # index 1: level_2
                    # index 2: level_3
                    catalog_name = "_".join(catalog['ParentCatalogNames'])
                    catalog_name = f"{catalog_name}_{catalog['Name']}" if catalog_name else catalog['Name']
                    conf[f"spark.sql.catalog.{catalog_name}"] = "org.apache.iceberg.spark.SparkCatalog"
                    conf[f"spark.sql.catalog.{catalog_name}.catalog-impl"] \
                        = "org.apache.iceberg.aws.glue.GlueCatalog"
                    conf[f"spark.sql.catalog.{catalog_name}.glue.id"] = f"{catalog['CatalogId']}"
                    conf[f"spark.sql.catalog.{catalog_name}.glue.account-id"] = f"{get_account_id_from_arn(catalog['ResourceArn'])}"
                    conf[f"spark.sql.catalog.{catalog_name}.glue.catalog-arn"] = f"{catalog['ResourceArn']}"
                    conf[f"spark.sql.catalog.{catalog_name}.glue.endpoint"] = self.glue_endpoint
                    conf[f"spark.sql.catalog.{catalog_name}.client.region"] = self.region
                    if self._is_fta_supported():
                        conf[f"spark.sql.catalog.{catalog_name}.glue.lakeformation-enabled"] = "true"
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                SageMakerConnectionDisplay.send_error(
                    "Lakehouse catalog configurations could not be automatically added because your role does not have "
                    "the necessary permissions to call glue:getCatalogs. Please verify your permissions.")
            else:
                raise e

    def _set_auto_add_catalogs(self, val):
        new_auto_add_catalogs = False if val.casefold() == "false" else True
        if self.auto_add_catalogs != new_auto_add_catalogs:
            # Regenerate spark_configurations if auto_add_catalogs is changed
            self.auto_add_catalogs = new_auto_add_catalogs

    def _set_iceberg_enabled(self, val: bool):
        if self.iceberg_enabled != val:
            # Regenerate spark_configurations if iceberg_enabled is changed
            self.iceberg_enabled = val
            self._gen_default_spark_configuration()
            self._update_spark_configuration_to_connection_default(self.connection_details)

    def _update_spark_configuration_to_connection_default(self, connection: SparkConnection):
        if hasattr(connection, 'spark_configs') and isinstance(connection.spark_configs, dict):
            self.default_spark_configuration.update(connection.spark_configs)
        else:
            self.logger.warning(f"spark_configs not found in connection {connection}")

    def _if_lake_formation_error(self, error_message: str) -> bool:
        if "org.apache.spark.fgac.error" in error_message:
            return True
        else:
            return False

    def _lakeformation_session_level_setting_supported(self) -> bool:
        return False

    def get_lakeformation_config_suggestion(self):
        if not self._lakeformation_session_level_setting_supported():
            return None
        if self.connection_type == CONNECTION_TYPE_SPARK_GLUE:
            configure = "\"--enable-lakeformation-fine-grained-access\" : \"false\""
        elif self.connection_type == CONNECTION_TYPE_SPARK_EMR_SERVERLESS:
            configure = """"conf": {
        "spark.emr-serverless.lakeformation.enabled": "false"
    }"""
        else:
            return None

        content = f"""%%configure --name {self.connection_name} --f
{{
    {configure}
}}"""
        return content

    def handle_spark_error(self, error_message: str, interactive_debugging: bool=True) -> None:
        try:
            cell_id = get_cell_id()
            cell_content = get_cell_content()
                
            if self.debugging_helper and interactive_debugging and cell_id:    
                application_id = self.get_app_id()
                self.logger.info(f"handle cell for cell_id : {cell_id}, application_id : {application_id}")
                self.debugging_helper.write_debugging_info(cell_id=cell_id, 
                                                           cell_content=cell_content,
                                                           application_id=application_id, 
                                                           error_message=error_message)

            
        except Exception as e:
            self.logger.error(f"unable to write_debugging_info because of : {e}")

        if self._if_lake_formation_error(error_message):
            # define output widgets for use with the button
            output = widgets.Output()
            output.layout.height = "0dp"
            output.add_class("lake-formation-error-helper")

            # define html widget to show hyperlink to public doc
            learn_more_message_widget = widgets.HTML(
                value="""<p>Learn more about <a target="_blank" rel="noopener noreferrer" href="https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/jupyterlab.html" style="color: #64B5F6">Jupyter compute and permission modes</a><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M6.83333 4.5V5.66667H3.91667V12.0833H10.3333V9.16667H11.5V12.6667C11.5 12.9888 11.2388 13.25 10.9167 13.25H3.33333C3.01117 13.25 2.75 12.9888 2.75 12.6667V5.08333C2.75 4.76117 3.01117 4.5 3.33333 4.5H6.83333ZM13.25 2.75V7.41667H12.0833L12.0833 4.74092L7.53747 9.28747L6.71252 8.46252L11.2579 3.91667H8.58333V2.75H13.25Z" fill="#64B5F6"/>
</svg>.
</p>""")
            learn_more_message_widget.add_class("lake-formation-error-helper")

            # define Javascript that will copy to clipboard
            copy_js = Javascript(
                f"navigator.clipboard.writeText({json.dumps(self.get_lakeformation_config_suggestion())})")

            # define Javascript that will change the style
            # running this javascript will:
            # add "jp-RenderedText" class and update mimeType for the custom type "lake-formation-error-helper"
            # by adding that all the lake-formation-error-helper class item to show in error stype in jupyter
            show_in_error_js = Javascript(f"""var elements = document.getElementsByClassName("lake-formation-error-helper");
            for (var i = 0; i < elements.length; i++) {{
                elements[i].parentNode.dataset.mimeType = 'application/vnd.jupyter.stderr'
                elements[i].parentNode.classList.add("jp-RenderedText")
            }}""")

            # define copy command button
            def on_clicked(_: widgets.Button) -> None:
                output.layout.visibility = "hidden"
                output.layout.display = "none"
                with output:
                    display(copy_js)

            button = widgets.Button(description="Copy command")
            button.on_click(on_clicked)
            button.add_class("lake-formation-error-helper")

            # display helper
            SageMakerConnectionDisplay.send_error(
                "The cell failed to run, verify your compute permissionMode is set to compatibility.\n")
            SageMakerConnectionDisplay.send_error("To change your compute permissionMode, follow these steps:\n")

            if self.get_lakeformation_config_suggestion():
                SageMakerConnectionDisplay.send_error(
                    "1. For the current cell, select a compute that is configured with permissionMode = compatibility")
                SageMakerConnectionDisplay.send_error("2. Re-run the cell\n")
                SageMakerConnectionDisplay.send_error("alternatively, you can:\n")
                SageMakerConnectionDisplay.send_error("1. Insert a new cell above")
                SageMakerConnectionDisplay.send_error("2. Copy and paste the %%configure magic command below")
                SageMakerConnectionDisplay.send_error("3. Insert command into the cell")
                SageMakerConnectionDisplay.send_error("4. Select the compute type of the cell to be \"Local Python\"")
                SageMakerConnectionDisplay.send_error("5. Run the new cell and any impacted cells\n")
                SageMakerConnectionDisplay.send_error(f"Command:\n\n{self.get_lakeformation_config_suggestion()}")
                display(button, output)
            else:
                SageMakerConnectionDisplay.send_error(
                    "1. For the current cell, select a compute that is configured with permissionMode = compatibility")
                SageMakerConnectionDisplay.send_error("2. Re-run the cell")

            display(learn_more_message_widget)
            display(show_in_error_js)

        SageMakerConnectionDisplay.send_error(error_message)
        raise ExecutionException(f"Code execution failed")

    
    def get_app_id(self) -> str | None:
        return None

    def get_s3_store(self):
        if self.s3_variable_manager_name is None:
            s3_variable_manager_name = "_s3_variable_manager_" + uuid.uuid4().hex

            # Create S3VariableManager in remote
            statement = f"""{s3_variable_manager_name} = S3VariableManager(project_s3_path=\"{PROJECT_S3_PATH}\")"""
            statement_response = self.run_statement(cell=statement, language=Language.python)

            if statement_response != "" and statement_response is not None:  # create compute also stores any warnings
                self.logger.warning(f"Warnings from s3 store handler creation: {statement_response}")
                raise UsageError(f"Warnings from s3 store handler creation: {statement_response}")

            self.s3_variable_manager_name = s3_variable_manager_name

        return self.s3_variable_manager_name

    def _get_profile_and_region(self):
        return {
            'region': self.connection_details.region,
            'profile': self.connection_details.connection_id
        }

    def create_session(self):
        self.pre_session_creation()
        self.create_session_operate()
        self.post_session_creation()

    def prepare_spark_configuration(self):
        # prepare spark configuartion
        self._gen_default_spark_configuration()
        self._update_spark_configuration_to_connection_default(self.connection_details)

    def pre_session_creation(self):
        self.prepare_spark_configuration()

    def create_session_operate(self):
        pass

    def post_session_creation(self):
        if self.debugging_helper:
            self.debugging_helper.prepare_session_in_seperate_thread()
            
        try:
            # upload required libs for display and data sharing
            import importlib.resources as resources
            from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager import __name__ as pkg_name

            compute_path = resources.files(pkg_name) / "s3_manager" / "s3_variable_manager.py"
            with compute_path.open() as f:
                s3_variable_manager_class_code = f.read()
                self.run_statement(cell=s3_variable_manager_class_code, language=Language.python, interactive_debugging=False)
        except Exception as e:
            self.logger.error(f"Unable to initialize s3 manager in session {e.__class__.__name__}: {e}")

        try:
            compute_path = resources.files(pkg_name) / "display" / "spark_display_compute.py"

            # SEND COMPUTE UTILS TO COMPUTE
            with compute_path.open() as f:
                display_magic_compute_class_code = f.read()
                self.run_statement(cell=display_magic_compute_class_code, language=Language.python, interactive_debugging=False)
        except Exception as e:
            SageMakerConnectionDisplay.send_error("Unable to initialize display compute resources in session");
            self.logger.error(f"Unable to initialize display compute resources in session {e.__class__.__name__}: {e}")
