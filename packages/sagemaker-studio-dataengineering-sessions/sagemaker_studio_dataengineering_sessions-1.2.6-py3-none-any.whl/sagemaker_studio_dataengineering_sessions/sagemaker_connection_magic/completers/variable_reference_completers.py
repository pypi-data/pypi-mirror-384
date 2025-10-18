import logging

from IPython import get_ipython
from IPython.core.completer import context_matcher, CompletionContext, SimpleCompletion

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import \
    CONNECTION_MAGIC_CONFIGURE

logger = logging.getLogger(__name__)


@context_matcher()
def variable_reference_matcher(context: CompletionContext):
    # Check if the cell starts with %%configure
    if not context.full_text.lstrip().startswith(CONNECTION_MAGIC_CONFIGURE):
        return None
    # Early return if not in ${} context
    if not is_in_variable_context(context.text_until_cursor):
        return None

    # Get variables from IPython
    ipython = get_ipython()
    user_ns = ipython.user_ns

    user_variables = [var for var in user_ns.keys()
                      if not var.startswith('_') and
                      isinstance(var, str)]

    completions = []
    for var_name in user_variables:
        if context.token in var_name:
            completions.append(SimpleCompletion(text=var_name, type="Variable"))

    return dict(completions=completions, suppress=True)


def is_in_variable_context(text_until_cursor: str) -> bool:
    if '${' not in text_until_cursor:
        return False

    last_dollar = text_until_cursor.rfind('${')
    if '}' in text_until_cursor[last_dollar:]:
        return False

    return True
