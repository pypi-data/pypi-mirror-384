import logging
import re

from IPython.core.completer import context_matcher, CompletionContext, SimpleCompletion
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_toolkit_utils import \
    SageMakerToolkitUtils

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    (CONNECTION_TYPE_GENERAL_SPARK, CONNECTION_TYPE_REDSHIFT, CONNECTION_TYPE_ATHENA,
     CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT, CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG,
     CONNECTION_MAGIC_PYSPARK, CONNECTION_MAGIC_SCALASPARK, CONNECTION_MAGIC_SQL, CONNECTION_MAGIC_CONFIGURE)

logger = logging.getLogger(__name__)


@context_matcher()
def connection_name_matcher(context: CompletionContext):
    full_text = context.full_text

    completions = []
    type_connection_name_mapping = SageMakerToolkitUtils.get_connection_type_mapping()
    toPromptConnection = promptConnectionActivated(context.text_until_cursor, context.cursor_line)
    if toPromptConnection and full_text.startswith(CONNECTION_MAGIC_PYSPARK + " "):
        spark_list = type_connection_name_mapping.get(CONNECTION_TYPE_GENERAL_SPARK)
        for name in spark_list:
            if context.token in name:
                completions.append(SimpleCompletion(text=name, type="Spark"))
    if toPromptConnection and (full_text.startswith(CONNECTION_MAGIC_SQL + " ")
                               or full_text.startswith(CONNECTION_MAGIC_CONFIGURE + " ")):
        spark_list = type_connection_name_mapping.get(CONNECTION_TYPE_GENERAL_SPARK)
        for name in spark_list:
            if context.token in name:
                completions.append(SimpleCompletion(text=name, type="Spark"))
        redshift_list = type_connection_name_mapping.get(CONNECTION_TYPE_REDSHIFT)
        for name in redshift_list:
            if context.token in name:
                completions.append(SimpleCompletion(text=name, type="Redshift"))
        athena_list = type_connection_name_mapping.get(CONNECTION_TYPE_ATHENA)
        for name in athena_list:
            if context.token in name:
                completions.append(SimpleCompletion(text=name, type="Athena"))
    if toPromptConnection and full_text.startswith(CONNECTION_MAGIC_SCALASPARK + " "):
        spark_list = type_connection_name_mapping.get(CONNECTION_TYPE_GENERAL_SPARK)
        for name in spark_list:
            if context.token in name:
                completions.append(SimpleCompletion(text=name, type="Spark"))
    return dict(completions=completions, suppress=True)


def promptConnectionActivated(textUntilCursor: str, cursor_line: int) -> bool:
    if cursor_line != 0:
        return False
    if (not textUntilCursor.startswith(CONNECTION_MAGIC_PYSPARK + " ")
            and not textUntilCursor.startswith(CONNECTION_MAGIC_SCALASPARK + " ")
            and not textUntilCursor.startswith(CONNECTION_MAGIC_SQL + " ")
            and not textUntilCursor.startswith(CONNECTION_MAGIC_CONFIGURE)):
        return False
    # combine all the multiple spaces to single space
    combined_spaces_text = re.sub(r'\s+', ' ', textUntilCursor)
    # find the last index of space
    index_of_last_space = combined_spaces_text.rfind(" ")

    # determine if to suggest connection name for %%configure:
    # we only suggest when there is argument and the argument before is -n or --name
    if textUntilCursor.startswith(CONNECTION_MAGIC_CONFIGURE):
        if (combined_spaces_text[
            index_of_last_space - len(" " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT):index_of_last_space]
                == " " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT
                or combined_spaces_text[
                   index_of_last_space - len(" " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG):index_of_last_space]
                == " " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG):
            return True
        else:
            return False

    # determine if to suggest connection name for %%pyspark, %%scalaspark, %%sql
    # we only suggest when there is no arguments specified or the argument before is -n or --name
    if (combined_spaces_text.count(" ") == 1
            or combined_spaces_text[
               index_of_last_space - len(" " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT):index_of_last_space]
            == " " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_SHORT
            or combined_spaces_text[
               index_of_last_space - len(" " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG):index_of_last_space]
            == " " + CONNECTION_MAGIC_ARGUMENT_CONNECTION_NAME_LONG):
        return True
    return False