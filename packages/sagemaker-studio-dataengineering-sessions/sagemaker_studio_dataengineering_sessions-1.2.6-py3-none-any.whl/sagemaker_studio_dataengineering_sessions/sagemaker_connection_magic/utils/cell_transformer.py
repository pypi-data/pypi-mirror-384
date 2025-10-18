from IPython import get_ipython
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import GET_IPYTHON_SHELL
import re

from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import NotAllowedSecondaryMagicException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay

from .constants import SUPPORTED_MAGICS, LANGUAGE_SUPPORTED_MAGICS
import sqlparse

"""
This function recollect a cell that is represented by a string
in to a list of code blocks, seprated by ipython shell code

If a line of code is transformed to be start with "get_ipython()",
the line is a special syntax understandable by ipython shell(e.g. line magic, cell magic) 
it will be keep as is as its own code block.
If a line of code is transformed to pure code, it will be collected to be part of a code block.

e.g. 
======before collect_cell_lines_to_code_blocks=======
a = 1
b = 2
%ls
c = 3
d = 4

======after collect_cell_lines_to_code_blocks========
a = 1, b = 2
get_ipython().run_line_magic('ls','')
c = 3, d = 4

"""


def collect_cell_lines_to_code_blocks(cell: str) -> list[str]:
    transformed_cell = get_ipython().transform_cell(cell)
    if "get_ipython().run_cell_magic(" in transformed_cell:
        raise NotAllowedSecondaryMagicException("Cell magic is not supported under current magic.")
    if "get_ipython().run_line_magic(" not in transformed_cell:
        return [cell]
    lines = transformed_cell.split("\n")
    # remove trailing empty lines
    while lines[-1] == "":
        lines.pop()
    code_blocks = []
    last_block = ""
    for line in lines:
        if line.startswith(GET_IPYTHON_SHELL):
            if last_block != "":
                code_blocks.append(last_block)
                last_block = ""
            code_blocks.append(line)
        else:
            last_block = last_block + line + "\n"
    if last_block != "":
        code_blocks.append(last_block)
    return code_blocks


def insert_info_to_block(code_block, connection_name, language) -> str:
    magic_patterns = {
        "line": r"get_ipython\(\)\.run_line_magic\('(.*?)',\s*'(.*?)'\)",
        "cell": r"get_ipython\(\)\.run_cell_magic\('(.*?)',\s*'(.*?)',\s*'(.*?)'\)"
    }

    for magic_type, pattern in magic_patterns.items():
        match = re.match(pattern, code_block)
        if match:
            magic_name = match.group(1)
            magic_args = match.group(2)
            if not _is_secondary_magic_supported(magic_name):
                raise NotAllowedSecondaryMagicException(
                    f"{magic_type.capitalize()} magic {magic_name} is not supported under current "
                    f"connected compute {connection_name}."
                )
            updated_args = _process_argument(magic_args, connection_name, r'(-n\s+|--name\s+)(\S+)', "--name")
            if _is_language_supported_magic(magic_name):
                updated_args = _process_argument(updated_args, language, r'(-l\s+|--language\s+)(\S+)', "--language")
            if magic_type == "line":
                return f"get_ipython().run_line_magic('{magic_name}', '{updated_args}')"
            else:  # cell magic
                magic_content = match.group(3)
                command = f"get_ipython().run_cell_magic('{magic_name}', '{updated_args}', '{magic_content}')"
                raise NotAllowedSecondaryMagicException("Cell magic is not supported under current magic.")

        # If no match is found, raise a ValueError
    raise ValueError("The provided magic code block does not match any recognized magic patterns.")


def extract_sql_queries_from_cell(cell) -> list[str]:
    # Strip comments from query and split query into multiple statements
    formatted_query = sqlparse.format(cell, strip_comments=True)
    sql_statements = sqlparse.split(formatted_query, strip_semicolon=True)

    # Parse SQL statements
    parsed_statements = []
    for statement in sql_statements:
        parsed_statement = sqlparse.parse(statement)
        new_statement = parsed_statement[0].value
        parsed_statements.append(new_statement)

    return parsed_statements


def _process_argument(args: str, target_argument_value: str, regex_pattern: str, argument_flag: str) -> str:
    """
        Processes the arguments string to ensure it contains the correct information.

        Parameters:
            args (str): The string of arguments.
            target_argument_value (str): the target value of the argument. e.g. the default.spark_glue
            regex_pattern (str): the regex pattern to find the value for the argument.
                                e.g. r'(-n\s+|--name\s+)(\S+)' [to match -n connection_name or --name connection_name]
            argument_flag (str): the flag to use with the target argument, e.g. --name [for flag the connection name]


        Returns:
            str: The updated arguments string.
        """
    pattern = re.compile(regex_pattern)
    match = pattern.search(args)

    if match:
        # If there's a match, check the name value in the second group
        # as the first group is the the flag, e.g. -l or --language/-n or --language
        current_argument = match.group(2)
        if current_argument != target_argument_value:
            SageMakerConnectionDisplay.write_msg(f"Current magic can only be allowed to use {target_argument_value}. "
                                               f"Changing to {target_argument_value}.")
            # Replace the existing name with the provided name
            args = pattern.sub(f'\\1{target_argument_value}', args)
    else:
        # If no -n or --name found, append -n and the provided name
        if args:
            args = f"{argument_flag} {target_argument_value} " + args
        else:
            args = f"{argument_flag} {target_argument_value}"

    return args


def _is_secondary_magic_supported(magic) -> bool:
    """
    Check if current magic is supported under %%connect

    Parameters:
        magic (str): The string of magic.

    SUPPORTED_MAGICS is a list of secondary magics we allow to be invoked under %%connect
    """
    return magic in SUPPORTED_MAGICS

def _is_language_supported_magic(magic) -> bool:
    """
    Check if current magic to support --language/-l as argument
    :param magic: The string of magic.
    :return: true if the magic support --language/-l or false otherwise
    """
    return magic in LANGUAGE_SUPPORTED_MAGICS
