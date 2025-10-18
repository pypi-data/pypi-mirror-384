import ast
import atexit
import logging
import signal
import uuid
from typing import Optional

import sqlparse
import sys
from datetime import datetime
import re

from IPython import get_ipython
from IPython.core.magic import magics_class, cell_magic, line_magic, Magics
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
from IPython.core.error import UsageError
from .cell_actions import CellActions
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.base_session_manager import BaseSessionManager
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    CONNECTION_TYPE_SPARK_EMR_EC2, CONNECTION_TYPE_SPARK_GLUE, DEFAULT_IPYTHON_NAME, \
    Language, CONNECTION_TYPE_ATHENA, SAGEMAKER_DEFAULT_CONNECTION_NAME_EXPRESS, \
    CONNECTION_TYPE_REDSHIFT, SAGEMAKER_DEFAULT_CONNECTION_NAME, CONNECTION_TYPE_IAM, GET_IPYTHON_SHELL, \
    CONNECTION_TYPE_SPARK_EMR_SERVERLESS, CONNECTION_TYPE_SPARK, CONNECTION_TYPE_NOT_SPARK, \
    CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG, CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import \
    SageMakerConnectionDisplay
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import \
    NoSessionException, \
    StopSessionException, ConnectionNotSupportedException, ConnectionNotFoundException, SessionExpiredError, \
    ExecutionException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import \
    SageMakerToolkitUtils
from sagemaker_studio_dataengineering_sessions.sagemaker_connection_magic.utils.constants import HELP_TEXT
from sagemaker_studio_dataengineering_sessions.sagemaker_connection_magic.utils.cell_transformer import \
    collect_cell_lines_to_code_blocks, insert_info_to_block
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.athena.athena_session import \
    AthenaSession
from IPython.display import display
from sagemaker_studio_dataengineering_sessions.sagemaker_database_session_manager.redshift.redshift_session import \
    RedshiftSession
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_ec2.emr_on_ec2_session import \
    EmrOnEc2Session
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.emr_session_manager.emr_on_serverless.emr_on_serverless_session import \
    EmrOnServerlessSession
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.glue_session_manager.glue_session import \
    GlueSession
from sagemaker_studio_dataengineering_sessions.sagemaker_spark_session_manager.spark_session_manager.spark_session import \
    SparkSession
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import \
    NotAllowedSecondaryMagicException
from sagemaker_studio_dataengineering_sessions.sagemaker_ipython_session_manager.ipython_session import IpythonSession
from sparkmagic.livyclientlib.exceptions import HttpClientException

from .utils.cell_transformer import extract_sql_queries_from_cell
from ..sagemaker_base_session_manager.common.constants import CONNECTION_NAME_OVERRIDES, PROJECT_S3_PATH
from ..sagemaker_base_session_manager.common.exceptions import ExecutionException

# Do not change this without updating the SageMakerDebuggingJLPlugin
CONNECT_MAGIC_STATS = "Connection: {} | Run start time: {} | Run duration : {}s."


def with_query_storage(func):
    func = argument("--query-storage",
                    default=None,
                    type=str,
                    help="TBD")(func)
    return func


def with_line_magic_args(func):
    func = argument("--name",
                    "-n",
                    help="The connection to be used. Will be parsed from cell")(func)
    func = argument("--language",
                    "-l",
                    default=Language.python.name,
                    help="The language to be used. Only python supported currently")(func)
    return func


@magics_class
class SageMakerConnectionMagic(Magics):
    def __init__(self, shell):
        super(SageMakerConnectionMagic, self).__init__(shell)
        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._handle_signal)
        self.logger = logging.getLogger(__name__)
        try:
            self.default_connection_name = SageMakerToolkitUtils._get_default_connection_name()
        except:
            SageMakerConnectionDisplay.send_error(f"Failed to retrieve default connection name. {e.__class__.__name__}: {e}")
            self.logger.warning(f"Falling back to default IPython name: {DEFAULT_IPYTHON_NAME}")
            self.default_connection_name = DEFAULT_IPYTHON_NAME
        # Initial session mapping with ipython Session        
        self._connection_session_mapping = {}
        try:
            self._connection_session_mapping[self.default_connection_name] = IpythonSession(
                connection_name=self.default_connection_name)
        except:
            SageMakerConnectionDisplay.send_error(f"Failed to initialize default IPython session. {e.__class__.__name__}: {e}")
            self.logger.error(f"Failed to initialize default IPython session. {e.__class__.__name__}: {e}")
            

    def with_data_sharing_magic_args(func):
        func = argument(
            "variable_names",
            nargs='?',
            help="Alternative way to specify variables to upload (Example: name1,name2) Note: Cannot be used together with --variable/-v option"
        )(func)
        func = argument(
            "--variable",
            "-v",
            default=None,
            help="Specify one or more variable names to upload to S3, using commas to separate multiple variables (Example: -v name1,name2)"
        )(func)
        func = argument(
            "--namespace",
            "-ns",
            default=None,
            help="Specify a custom namespace to store and share variables across notebooks and spaces, or leave empty to use the default kernel ID as namespace."
        )(func)
        return func

    @line_magic
    @magic_arguments()
    @with_data_sharing_magic_args
    @argument(
        "--force",
        "-f",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="Override existing variables in S3 storage (without this flag, existing variables won't be overwritten)."
    )
    @with_line_magic_args
    def push(self, line):
        args = self._parse_data_sharing_args(self.push, line)
        if args.language != Language.python.name:
            raise UsageError(f"The %push magic doesn't support language {args.language}.")

        namespace = self._get_namespace(args.namespace)
        session_manager = self._get_python_session_manager(sagemaker_connection_name=args.name)
        self._create_session_if_not_exist(session_manager, args.name)
        s3_variable_manager_name = session_manager.get_s3_store()
        for variable in args.variable:
            statement = f"""{s3_variable_manager_name}.push({variable}, \"{variable}\", \"{namespace}\", {args.force})"""
            try:
                session_manager.run_statement(cell=statement, language=Language.python)
            except ValueError as e:
                # convert ValueError to ipython UsageError (no stacktrace)
                raise UsageError(str(e))

    @line_magic
    @magic_arguments()
    @with_data_sharing_magic_args
    @with_line_magic_args
    def pop(self, line):
        args = self._parse_data_sharing_args(self.pop, line)
        if args.language != Language.python.name:
            raise UsageError(f"The %push magic doesn't support language {args.language}.")

        namespace = self._get_namespace(args.namespace)
        session_manager = self._get_python_session_manager(sagemaker_connection_name=args.name)
        self._create_session_if_not_exist(session_manager, args.name)
        s3_variable_manager_name = session_manager.get_s3_store()
        for variable in args.variable:
            statement = f"""{variable}={s3_variable_manager_name}.pop(\"{variable}\", \"{namespace}\")"""
            session_manager.run_statement(cell=statement, language=Language.python)

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be queried. "
    )
    def spark(self, line, cell):
        self.pyspark(line, cell)

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The compute to be run against. "
    )
    def pyspark(self, line, cell):
        args = None
        try:
            args = parse_argstring(self.pyspark, line)
        except:
            pass
        if args and args.name:
            connection_name = args.name
        elif line:
            # if no args.name found, try the whole line as connection_name.
            connection_name = line
        elif SageMakerToolkitUtils._get_default_spark_connection_name():
            connection_name = SageMakerToolkitUtils._get_default_spark_connection_name()
        else:
            SageMakerConnectionDisplay.send_error("Could not find a compute to run. Please specify the compute.")
            return

        if (CONNECTION_TYPE_SPARK_EMR_EC2 != SageMakerToolkitUtils.get_connection_type(connection_name)
            and CONNECTION_TYPE_SPARK_EMR_SERVERLESS != SageMakerToolkitUtils.get_connection_type(connection_name)
            and CONNECTION_TYPE_SPARK_GLUE != SageMakerToolkitUtils.get_connection_type(connection_name)):
            SageMakerConnectionDisplay.send_error(f"{connection_name} is not supported to run spark.")
            return
        try:
            self._connect(connection_name, "python", cell)
        except Exception as e:
            raise e.with_traceback(None)

    @cell_magic
    @magic_arguments()
    @argument(
        CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG,
        CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT,
        help="The compute to be run against. "
    )
    def scalaspark(self, line, cell):
        args = None
        try:
            args = parse_argstring(self.scalaspark, line)
        except:
            pass
        if args and args.name:
            connection_name = args.name
        elif line:
            # if no args.name found, try the whole line as connection_name.
            connection_name = line
        elif SageMakerToolkitUtils._get_default_spark_connection_name():
            connection_name = SageMakerToolkitUtils._get_default_spark_connection_name()
        else:
            SageMakerConnectionDisplay.send_error("Could not find a compute to run. Please specify the compute.")
            return
        try:
            self._connect(connection_name, "scala", cell)
        except Exception as e:
            raise e.with_traceback(None)

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The compute to be run against. "
    )
    def python(self, line, cell):
        self.local(line, cell)

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The compute to be run against. "
    )
    def local(self, line, cell):
        args = None
        try:
            args = parse_argstring(self.local, line)
        except:
            pass
        if args and args.name:
            connection_name = args.name
        elif line:
            # if no args.name found, try the whole line as connection_name.
            connection_name = line
        else:
            connection_name = self.default_connection_name
        if CONNECTION_TYPE_IAM != SageMakerToolkitUtils.get_connection_type(connection_name):
            SageMakerConnectionDisplay.send_error(f"{connection_name} is not supported to run in local.")
            return
        try:
            self._connect(connection_name, "python", cell)
        except Exception as e:
            raise e.with_traceback(None)

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be queried. "
    )
    def sql(self, line, cell):
        args = None
        try:
            args = parse_argstring(self.sql, line)
        except:
            pass
        if args and args.name:
            connection_name = args.name
        elif line:
            # if no args.name found, try the whole line as connection_name.
            connection_name = line
        elif SageMakerToolkitUtils._get_default_sql_connection_name():
            connection_name = SageMakerToolkitUtils._get_default_sql_connection_name()
        elif SageMakerToolkitUtils._get_default_spark_connection_name():
            connection_name = SageMakerToolkitUtils._get_default_spark_connection_name()
        else:
            SageMakerConnectionDisplay.send_error("Could not find a compute to run. Please specify the compute.")
            return
        try:
            self._connect(connection_name, "sql", cell)
        except Exception as e:
            raise e.with_traceback(None)

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be disconnected. "
    )
    def disconnect(self, line):
        args = parse_argstring(self.disconnect, line)
        connection_name = args.name
        if connection_name not in self._connection_session_mapping:
            SageMakerConnectionDisplay.send_error(
                f"Either {connection_name} is not a valid connection or it has been disconnected.")
            return

        session_manager = self._connection_session_mapping[connection_name]
        try:
            self.logger.info(f"Disconnecting connection: {connection_name}")
            session_manager.stop_session()
            self._connection_session_mapping.pop(connection_name)
            SageMakerConnectionDisplay.write_msg(f"Successfully disconnected connection: {connection_name}")
            self.logger.info(f"Successfully disconnected connection: {connection_name}")
        except StopSessionException as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to disconnect connection: {line}. Error: {e}. Please try again.")
            self.logger.error(f"Unable to disconnect connection: {connection_name}. Error: {e}. Please try again.")

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be disconnected. "
    )
    def matplot(self, line):
        args = None
        try:
            args = parse_argstring(self.matplot, line)
        except:
            pass
        if args and args.name:
            connection_name = args.name
        elif line:
            # if no args.name found, try the whole line as connection_name.
            connection_name = line
        else:
            SageMakerConnectionDisplay.send_error("Could not find a compute to run. Please specify the compute.")
            return

        match = re.match(r"(?:-n|--name)\s+(\S+)\s+(.*)", connection_name)
        try:
            connection_name = match.group(1)
            content = match.group(2)
        except Exception:
            # This can happen under a scenario when the line magic will be triggered under local
            # but without an actual connection name provided.
            SageMakerConnectionDisplay.send_error(
                f"Unable to invoke matplot magic as neither connection name nor the plot name provided.")
            self.logger.error(f"Unable to invoke matplot magic as neither connection name nor the plot name provided.")
            return

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)
        try:
            session_manager.matplot(content)
        except Exception as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to matplot for {connection_name}. Error: {e}")
            self.logger.error(f"Unable to matplot for {connection_name}. Error: {e}")
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be used. "
    )
    @argument(
        "--language",
        "-l",
        default="python",
        help="The language to be used. ")
    @argument(
        "--local",
        help="local var name")
    @argument(
        "--remote",
        "-r",
        help="remote var name")
    def send_to_remote(self, line):
        args = parse_argstring(self.send_to_remote, line)
        local_var = args.local
        remote_var = args.remote
        connection_name = args.name
        self._validate_connection_name(connection_name)
        language = args.language
        language_enum = Language[language]
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)
        try:
            self.logger.info(f"sending to remote. Local var: {local_var}, "
                             f"remote var: {remote_var}, "
                             f"connection: {connection_name}, "
                             f"language: {language}")
            session_manager.send_to_remote(local_var, remote_var, language_enum)
        except Exception as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to send variable to remote for connection: {connection_name}. Error: {e}")
            self.logger.error(f"Unable to send variable to remote for connection: {connection_name}. Error: {e}")
        return

    # Displays ALL connection sessions in current Kernel
    @line_magic
    def list_sessions(self, line):
        if not self._connection_session_mapping:
            # This won't be displayed but to complete code logic as all magics will happen under %%connect
            SageMakerConnectionDisplay.write_msg("Current Kernel doesn't have any active connection session.")
            return

        msgs = ["The following are active connection sessions under the current Kernel."]
        for connection_name in self._connection_session_mapping:
            connection_type = SageMakerToolkitUtils.get_connection_type(connection_name)
            if connection_type != CONNECTION_TYPE_IAM:
                msgs.append(f"{connection_name}: {connection_type}")
        if len(msgs) > 1:
            for msg in msgs:
                SageMakerConnectionDisplay.write_msg(msg)
        else:
            SageMakerConnectionDisplay.write_msg("Current Kernel doesn't have any active connection session.")

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be used. "
    )
    def info(self, line):
        args = parse_argstring(self.info, line)
        sagemaker_connection_name = args.name
        self._validate_connection_name(sagemaker_connection_name)

        session = self._connection_session_mapping.get(sagemaker_connection_name)
        if not session:
            SageMakerConnectionDisplay.display("There is no current session in the kernel.")
            return
        if not session.is_session_connectable():
            SageMakerConnectionDisplay.display(f"There is no active connectable {sagemaker_connection_name} "
                                               f"session in the kernel.")
            return

        try:
            session.get_info()
        except NotImplementedError:
            SageMakerConnectionDisplay.send_error(
                f"The info magic is not supported for connection: {sagemaker_connection_name}.")
        except Exception as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to get information for connection: {sagemaker_connection_name}. Error: {e}")
            # This will also be printed on the screen, but it shouldn't.
            # Tracked in SIM: https://issues.amazon.com/issues/V1492577404
            self.logger.error(f"Unable to get information for connection: {sagemaker_connection_name}. Error: {e}")
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be used. "
    )
    def session_id(self, line):
        args = parse_argstring(self.session_id, line)
        sagemaker_connection_name = args.name
        self._validate_connection_name(sagemaker_connection_name)

        session = self._connection_session_mapping.get(sagemaker_connection_name)
        if not session:
            SageMakerConnectionDisplay.display("There is no current session in the kernel.")
            return

        try:
            session.get_session_id()
        except NotImplementedError:
            SageMakerConnectionDisplay.send_error(
                f"The session_id magic is not supported for connection: {sagemaker_connection_name}.")
        except Exception as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to get session id for connection: {sagemaker_connection_name}. Error: {e}")
            # This will also be printed on the screen, but it shouldn't.
            # Tracked in SIM: https://issues.amazon.com/issues/V1492577404
            self.logger.error(f"Unable to get session id for connection: {sagemaker_connection_name}. Error: {e}")
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be used. "
    )
    def status(self, line):
        args = parse_argstring(self.status, line)
        connection_name = args.name
        self._validate_connection_name(connection_name)

        session = self._connection_session_mapping.get(connection_name)
        if not session:
            SageMakerConnectionDisplay.display("There is no current session in the kernel.")
            return

        try:
            session.get_status()
        except NotImplementedError:
            SageMakerConnectionDisplay.send_error(
                f"The status magic is not supported for connection: {connection_name}.")
        except Exception as e:
            SageMakerConnectionDisplay.send_error(
                f"Unable to get session status for connection: {connection_name}. Error: {e}")
            # This will also be printed on the screen, but it shouldn't.
            # Tracked in SIM: https://issues.amazon.com/issues/V1492577404
            self.logger.error(f"Unable to get session status for connection: {connection_name}. Error: {e}")
        return

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be queried.",
    )
    def tags(self, line, cell):
        args = parse_argstring(self.configure, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)

        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)
        session_manager.add_tags(cell)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be queried.",
    )
    def logs(self, line):
        args = parse_argstring(self.configure, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)
        session_manager.get_logs()
        return

    @cell_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be queried.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    def configure(self, line, cell):
        args = parse_argstring(self.configure, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)
        session_manager.configure(cell, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "prefix",
        type=str,
        help='The prefix value to set')
    def session_id_prefix(self, line):
        args = parse_argstring(self.session_id_prefix, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_session_id_prefix(args.prefix, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "version",
        type=str,
        help='The value to set')
    def glue_version(self, line):
        args = parse_argstring(self.glue_version, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_glue_version(args.version, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "number",
        type=str,
        help='The value to set')
    def number_of_workers(self, line):
        args = parse_argstring(self.number_of_workers, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_number_of_workers(args.number, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "type",
        type=str,
        help='The value to set')
    def worker_type(self, line):
        args = parse_argstring(self.worker_type, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_worker_type(args.type, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "value",
        type=str,
        help='The value to set')
    def idle_timeout(self, line):
        args = parse_argstring(self.idle_timeout, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_idle_timeout(args.value, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "configuration",
        type=str,
        help='The configuration value to set')
    def spark_conf(self, line):
        args = parse_argstring(self.spark_conf, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.spark_conf(args.configuration, args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    @argument(
        "type",
        type=str,
        help='The value to set')
    def session_type(self, line):
        args = parse_argstring(self.session_type, line)
        session_type = args.type

        content = f"-n {args.name}"
        if args.force:
            content = f"-n {args.name} -f"

        if session_type == "streaming":
            self.streaming(content)
        elif session_type == "etl":
            self.etl(content)
        else:
            SageMakerConnectionDisplay.send_error(f"Invalid session type value: {session_type}. "
                                                  f"Acceptable values are 'streaming' or 'etl'.")
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    def streaming(self, line):
        args = parse_argstring(self.streaming, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_session_type("streaming", args.force)
        return

    @line_magic
    @magic_arguments()
    @argument(
        "--name",
        "-n",
        help="The connection to be configured.",
    )
    @argument(
        "-f",
        "--force",
        type=bool,
        default=False,
        nargs="?",
        const=True,
        help="If present, user understands.",
    )
    def etl(self, line):
        args = parse_argstring(self.etl, line)
        connection_name = args.name

        self._validate_connection_name(connection_name)
        session_manager = self._add_connection_session_mapping_if_not_existent(connection_name)

        session_manager.set_session_type("etl", args.force)
        return

    @line_magic
    def help(self, line):
        SageMakerConnectionDisplay.display_markdown(HELP_TEXT)
        return

    # Display Magic
    @line_magic
    @magic_arguments()
    @with_query_storage
    @argument(
        "df",
        type=str,
        help="Variable name of Dataframe to display. Must be of pandas, spark, or pandas-on-spark type",
    )
    @argument(
        "--view",
        "-v",
        default="all",
        type=str,
        help="View of dataframe to display. Options: ['schema', 'table', 'plot', 'all']"
    )
    @argument(
        "--size",
        "-s",
        type=int,
        default=10000,
        help="Number of Rows to sample from the dataframe. Options: integer below 1,000,000"
    )
    @argument(
        "--method",
        "-m",
        default="head",
        type=str,
        help="Sampling Method to use. "
             "Options: ['head', 'tail', 'random', 'all' (size must be greater than dataframe size)]"
    )
    @argument(
        "--inference",
        "-i",
        type=bool,
        default=False,
        help="Use type inference to parse dataframe columns from string type to numeric type "
             "if all entries are numeric in nature. Options: [True, False]"
    )
    @argument(
        "--plot",
        "-p",
        type=str,
        default="default",
        help="Plot Library to use to display data. Options: ['default', 'pygwalker', 'dataprep', 'ydata-profiling']",
    )
    @argument(
        "--spark-use-threshold",
        type=int,
        default=1_000_000,
        help="Sets the threshold for which to use spark drivers to compute statistics. "
             "When the sample size is larger than this threshold, then PySpark is used to compute. "
             "Only applies when spark session is available",
    )
    @argument(
        "--max-sample",
        type=int,
        default=1_000_000_000,
        help="Sets the maximum sample size to compute statistics usable by the DisplayMagic."
    )
    @argument(
        "--graph-render-threshold",
        type=int,
        default=50_000,
        help="The maximum number of rows to display in the plotting view. "
             "If it is set to 50,000, the first 50,000 data points will be used for plotting if using external library plotting and, "
             "with the default plotting view, an LTTB downsampling to 50,000 points is performed and plotted from the sample. "
             "Default is 50,000. ")
    @argument(
        "--columns",
        "-c",
        type=str,
        nargs="*",
        default=None,
        help="Columns to display in column-specific view. Must be columns in dataframe seperated by a space. "
             "For example --columns <col1> <col2> ..."
    )
    @argument(
        "--name",
        "-n",
        help="The connection to be used. Will be parsed from cell",
    )
    @argument(
        "--language",
        "-l",
        default=Language.python.name,
        help="The language to be used. Only python supported currently"
    )
    def display(self, line):
        """
        Display dataframe view in the Jupyter output kernel to perform exploratory data analysis.

        In AWS SageMaker, dataframe types of pandas, spark, and pandas-on-spark can be displayed and summarized,
        with the schema view displaying intra-column statistics concerning columns within the dataframe, and
        the plot view providing visualizations of the data in the dataframe.

        By default, the plotting visualizations do not require any external dependencies. However, support is available for
        pygwalker, dataprep, and ydata. These plotting libraries can be selected by passing the --plot flag and must be installed
        by the user on their compute used by SageMaker. This allows the user to configure the display magic to their preference
        of library to perform exploratory data analysis.

        The --columns flag allows for the display of specific columns in the column-specific view. This is useful for displaying
        column-specific information about larger dataframes quickly.

        Usage:
            %display <df> [--view <view>] [--size <size>] [--method <method>] [--inference <inference>] [--plot <plot>] [--columns <columns>]
            %display?
        """

        args = parse_argstring(self.display, line)
        if not args.name:
            args.name = self.default_connection_name

        if args.language != Language.python.name:
            SageMakerConnectionDisplay.send_error(
                f"Invalid input error: language: {args.language} selected is not valid.")
            return

        session_manager = self._get_python_session_manager(sagemaker_connection_name=args.name)
        spark_available = self._spark_available(sagemaker_connection_name=args.name)
        storage = "s3" if self._is_s3_storage_default() else "cell"
        display_magic_render = session_manager.create_display_renderer(
            df=args.df,
            spark_session=spark_available,
            size=args.size,
            sampling_method=args.method,
            columns=args.columns,
            type_inference=args.inference,
            plot_lib=args.plot,
            spark_use_threshold=args.spark_use_threshold,
            max_sample=args.max_sample,
            graph_render_threshold=args.graph_render_threshold,
            storage=args.query_storage if args.query_storage else storage,
            enable_profiling=self._is_profiling_enabled()
        )
        # Render the Holoviz Panel output if it was successfully created
        if display_magic_render:
            display_magic_render.render()
        else:
            SageMakerConnectionDisplay.write_msg(
                f"Could not render rich display for {args.df}. Defaulting to output from connection.")
            self._run_statement_and_display_output(session_manager, args.df, Language.python)

    def _connect(self, connection_name: str, language: str, cell):
        # override connection_name with CONNECTION_NAME_OVERRIDES if exist
        if CONNECTION_NAME_OVERRIDES and connection_name in CONNECTION_NAME_OVERRIDES.keys():
            connection_name = CONNECTION_NAME_OVERRIDES[connection_name]
            SageMakerConnectionDisplay.write_msg(
                f"Use connection name: {connection_name} based on connection overrides.")

        language_enum = Language[language]
        start_time = datetime.now()
        connection_id = self._validate_sagemaker_connection_and_language(connection_name, language)
        if not connection_id:
            SageMakerConnectionDisplay.send_error(
                f"Invalid input error: Connection: {connection_name} and language: {language} selected is not valid.")
            raise ConnectionNotFoundException(
                f"Invalid input error: Connection: {connection_name} and language: {language} selected is not valid.")
        try:
            # Leave the connection existence validation in the connection magic.
            SageMakerToolkitUtils.get_connection_detail_from_id(connection_id)
        except:
            self.logger.warning(f"Unable to find region for connection: {connection_id} ")
            raise ConnectionNotFoundException(f"Unable to find region for connection: {connection_id} ")
        try:
   
            session_manager = self._add_connection_session_mapping_if_not_existent(connection_name, language_enum)
            CellActions.current_session_manager = session_manager
            if CONNECTION_TYPE_IAM == SageMakerToolkitUtils.get_connection_type(connection_name):
                # We only have one connection, which is of type CONNECTION_TYPE_IAM, the default IPython connection
                self.logger.info(f"Running statement for connection: {connection_name} with language: {language}")
                self._connection_session_mapping[connection_name].run_cell(cell)
                return

            # Throw error if the current session is using different language
            if not self._is_session_manager_language_valid(session_manager, language_enum):
                SageMakerConnectionDisplay.send_error(
                    f"Glue session already started in {session_manager.language.name}. If you intend to recreate the "
                    "session with new language, please stop current session using magic %%disconnect")
                raise ExecutionException(
                    f"Glue session already started in {session_manager.language.name}. If you intend to recreate the "
                    "session with new language, please stop current session using magic %%disconnect")
            else:
                self._parse_and_execute_cell(connection_name, language, cell, session_manager)
        finally:
            end_time = datetime.now()
            SageMakerConnectionDisplay.write_critical_msg(CONNECT_MAGIC_STATS.format(connection_name,
                                                                                     start_time,
                                                                                     end_time - start_time))
        return

    def _parse_and_execute_cell(self, connection_name: str, language: str, cell, session_manager) -> None:
        language_enum = Language[language]
        try:
            code_blocks = collect_cell_lines_to_code_blocks(cell)
        except NotAllowedSecondaryMagicException as e:
            SageMakerConnectionDisplay.send_error(f"{e} Please retry with allowed magics.")
            self.logger.error(f"{e} Please retry with allowed magics.")
            raise e.with_traceback(None)

        default_ipython_session_manager = self._connection_session_mapping[self.default_connection_name]
        for i in range(len(code_blocks)):
            if code_blocks[i].startswith(GET_IPYTHON_SHELL):
                # If cell line is started with "get_ipython()", execute the line with ipython
                try:
                    code_block_with_info_inserted = insert_info_to_block(code_blocks[i], connection_name, language)
                    default_ipython_session_manager.run_statement(cell=code_block_with_info_inserted)
                except NotAllowedSecondaryMagicException as e:
                    SageMakerConnectionDisplay.send_error(f"{e} Please retry with allowed magics.")
                    self.logger.error(f"{e} Please retry with allowed magics.")
                    raise e
            else:
                # If cell block is not started with "get_ipython()", execute the block using selected compute component
                try:
                    self.logger.info(f"Running statement for connection: {connection_name} with language: {language}")

                    match language_enum:
                        case Language.python:
                            # skip running in remote if all comment
                            if len(ast.parse(code_blocks[i]).body) == 0:
                                continue
                            # Session might be timeout or terminated with error
                            self._create_session_if_not_exist(session_manager, connection_name)
                            # For Python, only display dataframe in last line
                            # Do type analysis on last statement of last code block in a python cell
                            if i == len(code_blocks) - 1:
                                self._run_statement_and_display_output_and_dataframe(session_manager, code_blocks[i],
                                                                                     connection_name)
                            else:
                                self._run_statement_and_display_output(session_manager, code_blocks[i], language_enum)
                        case Language.sql:
                            # skip running in remote if all comment
                            if not sqlparse.format(code_blocks[i], strip_comments=True):
                                continue
                            # Session might be timeout or terminated with error
                            self._create_session_if_not_exist(session_manager, connection_name)
                            # For SQl, always display dataframe
                            self._run_sql_statement_and_display_output(session_manager, code_blocks[i], connection_name)
                        case _:
                            # Session might be timeout or terminated with error
                            self._create_session_if_not_exist(session_manager, connection_name)
                            # For other language (only scala as for now), execute the statement directly
                            self._run_statement_and_display_output(session_manager, code_blocks[i], language_enum)
                except NoSessionException as e:
                    SageMakerConnectionDisplay.send_error(f"No session exists for connection: {connection_name}. "
                                                          f"Please try to rerun the cell or restart kernel. "
                                                          f"Error: {e}")
                    self.logger.error(f"No session exists for connection: {connection_name}. "
                                      f"Please try to rerun the cell or restart kernel. Error: {e}")
                    raise e
                except ExecutionException as e:
                    SageMakerConnectionDisplay.send_error(f"Unable to run statement for connection: {connection_name}. "
                                                          f"Error: {e}")
                    self.logger.error(f"Unable to run statement for connection: {connection_name}. Error: {e}")
                    raise e
                except Exception as e:
                    SageMakerConnectionDisplay.send_error(
                        f"Unable to run statement for connection: {connection_name}. Error: {e}")
                    self.logger.error(f"Unable to run statement for connection: {connection_name}. Error: {e}")
                    raise ExecutionException(f"Unable to run statement for connection: {connection_name}.")

    def _validate_connection_name(self, connection_name) -> str:
        # The connection name should be a valid one with a corresponding connection file created
        if not connection_name:
            raise ValueError("Connection name cannot be empty.")
        try:
            return SageMakerToolkitUtils.get_connection_type(connection_name)
        except ConnectionNotFoundException as e:
            SageMakerConnectionDisplay.send_error(f"Invalid connection name. "
                                                  f"Please make sure you have a valid connection to be configured. "
                                                  f"Error: {e}")

    def _display_output(self, output, session_manager, statement: str):
        if output is not None:
            class_name = re.findall(r"'(.*?)'", str(type(output)))[0]
            storage = "s3" if self._is_s3_storage_default() else "cell"
            # Parse dataframe type to determine display with display magic
            if (class_name == "pyspark.sql.dataframe.DataFrame" or class_name == "pyspark.pandas.DataFrame"
                or class_name == "pandas.core.frame.DataFrame"):
                # Handle DataFrame output using display render
                # Only applies to Athena and Redshift connections in current experience
                display_magic_render = session_manager.create_display_renderer(
                    df=output,
                    last_line_execution=True,
                    storage=storage,
                    project_s3_path=PROJECT_S3_PATH,
                    statement=statement
                )
                if display_magic_render:
                    display_magic_render.render()
                    return
            # Default to standard output if not a dataframe or if rich display cannot be rendered
            try:
                sys.stdout.write("{}\n".format(output))
                sys.stdout.flush()
            except:
                try:
                    display(output)
                except:
                    print(output)
            return

    def _add_connection_session_mapping_if_not_existent(self, sagemaker_connection_name: str, language=Language.python):
        """
        This method creates an AWS profile for the connection to be established if it's absent from the space.
        When the connection is not recorded in current kernel, it will also be initialized and recorded in the session mapping.
        """
        start_time = datetime.now()

        if sagemaker_connection_name in self._connection_session_mapping:
            return self._connection_session_mapping[sagemaker_connection_name]

        sagemaker_connection_type = SageMakerToolkitUtils.get_connection_type(sagemaker_connection_name)
        SageMakerConnectionDisplay.write_critical_msg(f"Executing for connection type: {sagemaker_connection_type}, "
                                                      f"connection name: {sagemaker_connection_name}")
        self.logger.info(
            f"Creating session object for connection type: {sagemaker_connection_type} connection name: {sagemaker_connection_name}")
        if CONNECTION_TYPE_SPARK_EMR_EC2 == sagemaker_connection_type:
            session = EmrOnEc2Session(connection_name=sagemaker_connection_name)
        elif CONNECTION_TYPE_SPARK_GLUE == sagemaker_connection_type:
            session = GlueSession(connection_name=sagemaker_connection_name, language=language)
        elif CONNECTION_TYPE_REDSHIFT == sagemaker_connection_type:
            session = RedshiftSession(connection_name=sagemaker_connection_name)
        elif CONNECTION_TYPE_ATHENA == sagemaker_connection_type:
            session = AthenaSession(connection_name=sagemaker_connection_name)
        elif CONNECTION_TYPE_SPARK_EMR_SERVERLESS == sagemaker_connection_type:
            session = EmrOnServerlessSession(connection_name=sagemaker_connection_name)
        elif CONNECTION_TYPE_IAM == sagemaker_connection_type:
            session = IpythonSession(connection_name=sagemaker_connection_name)
        else:
            raise ConnectionNotSupportedException(
                f'Maxdome connection type {sagemaker_connection_type} is currently not supported')
        self._connection_session_mapping[sagemaker_connection_name] = session
        self.logger.info(
            f"Created session object in session mapping for connection type: {sagemaker_connection_type} "
            f"connection name: {sagemaker_connection_name}. "
            f"Creation time: {datetime.now() - start_time}")
        return session

    def _validate_sagemaker_connection_and_language(self, sagemaker_connection_name: str, language: str) -> str | None:
        '''
        return connection id if connection and language is valid
        otherwise return None.
        '''
        connection_id = SageMakerToolkitUtils.get_connection_id_from_connection_name(sagemaker_connection_name)
        connection_type = self._validate_connection_name(sagemaker_connection_name)
        try:
            language_enum = Language[language]
            if not language_enum.supports_connection_type(connection_type):
                SageMakerConnectionDisplay.send_error(
                    f"Connection with name: {sagemaker_connection_name} does not support language: {language}.")
                return None
            return connection_id
        except KeyError:
            SageMakerConnectionDisplay.send_error(f"Language: {language} is invalid.")
            return None
        except ConnectionNotFoundException:
            SageMakerConnectionDisplay.send_error(f"Connection {sagemaker_connection_name} does not exist")
            return None

    def _cleanup(self):
        for sagemaker_connection_name, session_manager in self._connection_session_mapping.items():
            self.logger.info(f"Starting to clean up for {sagemaker_connection_name}")
            try:
                session_manager.stop_session()
            except Exception as e:
                self.logger.warning(f"Skipping cleanup {sagemaker_connection_name} because of {e}")
        self.logger.info("end of clean up")

    def _handle_signal(self, signum, frame) -> None:
        self.logger.info(f"Received signal: {signum}")
        self._cleanup()

    # Finds session manager to use that can operate Python code
    def _get_python_session_manager(self, sagemaker_connection_name):
        sagemaker_connection_type = SageMakerToolkitUtils.get_connection_type(sagemaker_connection_name)
        if sagemaker_connection_type in CONNECTION_TYPE_SPARK:
            return self._connection_session_mapping[sagemaker_connection_name]
        elif sagemaker_connection_type in CONNECTION_TYPE_NOT_SPARK:
            # Athena and Redshift do not support python, so use IAM connection for displaying output
            return self._connection_session_mapping[self.default_connection_name]
        raise NoSessionException

    # NOTE CAN BE REMOVED ONCE SPARKCONNECT IS AVAILABLE.
    # Determine whether there is a Spark instance available on the remote compute
    def _spark_available(self, sagemaker_connection_name):
        sagemaker_connection_type = SageMakerToolkitUtils.get_connection_type(sagemaker_connection_name)
        if sagemaker_connection_type in CONNECTION_TYPE_SPARK:
            return True
        return False

    def _run_statement_and_display_output_and_dataframe(self, session_manager, statement, connection_name) -> None:
        """
        run statement and display output using ipython output except the last line:
        1. If the last line is a dataframe, display the dataframe using display magic
        2. If the last line is not a dataframe, display output using ipython output
        :param session_manager: the session manager to be used to operate statement
        :param statement: the statement to be operated
        :param connection_name: the connection name to be used
        """
        # Parse the last statement in a cell with ast
        # This handles cases where the last line is a comment or part of a multiline function call
        last_block_ast = ast.parse(statement)
        if len(last_block_ast.body) == 0:
            return
        last_statement_ast = last_block_ast.body[-1]
        # Check if the last statement is an expression (either a variable name or function call without assignment)
        storage = "s3" if self._is_s3_storage_default() else "cell"
        if isinstance(last_statement_ast, ast.Expr):
            # Modify the last statement to store the value of the expression in a temp variable with a UUID suffix
            # Initialize the temp variable to None at the start of the code block to ensure that it is defined even when an Exception occurs
            var_name = '_temp_var_' + uuid.uuid4().hex
            last_code_block = f"{var_name} = None\n" + ast.unparse(
                last_block_ast.body[:-1]) + f"\n{var_name} = {ast.unparse(last_statement_ast)}"
            self._run_statement_and_display_output(session_manager, last_code_block, Language.python)
            # The temp variable holds the result of the last line of execution
            # This variable can be used to render the display if it is a dataframe
            display_magic_render = session_manager.create_display_renderer(
                df=var_name,
                last_line_execution=True,
                spark_session=self._spark_available(connection_name),
                storage=storage,
                statement=statement
            )
            if display_magic_render:
                display_magic_render.render()
                # Delete temporary variable after displaying it
                session_manager.run_statement(f"del {var_name}", Language.python)
            else:
                # Display the output of the temp variable if it is not a dataframe
                self._run_statement_and_display_output(session_manager, f"({var_name}, exec('del {var_name}'))[0]", Language.python)
        else:
            self._run_statement_and_display_output(session_manager, statement, Language.python)

    def _run_statement_and_display_output(self, session_manager, statement, language_enum) -> None:
        """
        run statement and display output using ipython output
        :param session_manager: the session manager to be used to operate statement
        :param statement: the statement to be operated
        :param language_enum: the Language enum to be used to set operate language
        :param connection_name: the connection name to be used
        """
        output = session_manager.run_statement(cell=statement, language=language_enum)
        self._display_output(output, session_manager, statement)

    def _run_sql_statement_and_display_output(self, session_manager, statement, connection_name) -> None:
        """
        split sql statement to separate queries and run separately.
        run queries and display dataframes using display magic.
        :param session_manager: the session manager to be used to operate sql statement
        :param statement: the sql statement to be operated
        :param connection_name: the connection name to be used
        """
        # split statement to queries
        queries = extract_sql_queries_from_cell(statement)
        if isinstance(session_manager, SparkSession):
            for query in queries:
                # For Glue session, additional steps are required to support display magic
                # Save SQL query result to _ and display it using the rich display
                spark_sql_code = f'_ = spark.sql("""{query}""")\n_'
                self._run_statement_and_display_output_and_dataframe(session_manager, spark_sql_code, connection_name)
        else:
            for query in queries:
                # For other sessions, df would be automatically handled.
                self._run_statement_and_display_output(session_manager, query.rstrip(), Language.sql)

    def _is_session_manager_language_valid(self, session_manager, expected_language: Language) -> bool:
        if not isinstance(session_manager, GlueSession):
            # Only Glue need different session for different language.
            return True

        if not session_manager.is_session_connectable():
            # If session is not started, change the session manager language
            session_manager.language = expected_language
            return True

        match expected_language:
            # python and sql are using python session
            case Language.python:
                if session_manager.language == Language.scala:
                    return False
                else:
                    return True
            case Language.sql:
                if session_manager.language == Language.scala:
                    return False
                else:
                    return True
            # scala is using scala session
            case Language.scala:
                if session_manager.language != Language.scala:
                    return False
                else:
                    return True

    def _create_session_if_not_exist(self, session_manager, connection_name) -> None:
        start_time = datetime.now()
        session_connectable = False
        try:
            session_connectable = session_manager.is_session_connectable()
        except (HttpClientException, NoSessionException, SessionExpiredError):
            self.logger.error(f"Session {connection_name} is expired or running into some issue.")

        if not session_connectable:
            self.logger.info(f"Starting session for connection: {connection_name}.")
            try:
                session_manager.create_session()
                self.logger.info(
                    f"Session created for connection: {connection_name}. Creation time: {datetime.now() - start_time}")
                SageMakerConnectionDisplay.write_msg(f"Session created for connection: {connection_name}.")
            except Exception as e:
                SageMakerConnectionDisplay.send_error(
                    f"Unable to create session for connection: {connection_name} because of "
                    f"{e.__class__.__name__}: {e}")
                return
        else:
            self.logger.info(
                f"Session creation not needed for connection: {connection_name}. Processing time: {datetime.now() - start_time}")

    def _parse_data_sharing_args(self, magic_func, line):
        args = parse_argstring(magic_func, line)
        if not args.name:
            args.name = self.default_connection_name
        if args.variable:
            if args.variable_names:
                raise UsageError(
                    f"unrecognized arguments: {args.variable_names}. Variables have already been defined using --variable or -v.")
        else:
            if args.variable_names:
                args.variable = args.variable_names
            else:
                raise UsageError(
                    "No variables specified. Use either positional arguments (example: %push var1,var2) or --variable/-v option (example: %push -v var1,var2)")
        args.variable = args.variable.split(',')
        return args

    def _get_namespace(self, namespace):
        if namespace:
            # use namespace if namespace is defined
            return namespace
        else:
            try:
                return get_ipython().kernel.ident
            except (NameError, AttributeError):
                raise UsageError("Namespace is required outside Jupyter Lab environment (use --namespace or -ns)")

    def _is_s3_storage_default(self):
        return get_ipython().user_ns.get("_sagemaker_visualization_use_s3_storage", False)

    def _is_profiling_enabled(self):
        return get_ipython().user_ns.get("_sagemaker_visualization_enable_profiling", False)
