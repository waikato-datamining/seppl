import os
import tempfile

from typing import List


VAR_HOME = "{HOME}"
VAR_CWD = "{CWD}"
VAR_TMP = "{TMP}"
VAR_INPUT_PATH = "{INPUT_PATH}"
VAR_INPUT_NAMEEXT = "{INPUT_NAMEEXT}"
VAR_INPUT_NAMENOEXT = "{INPUT_NAMENOEXT}"
VAR_INPUT_EXT = "{INPUT_EXT}"
VAR_INPUT_PARENT_PATH = "{INPUT_PARENT_PATH}"
VAR_INPUT_PARENT_NAME = "{INPUT_PARENT_NAME}"
VARIABLES = [
    VAR_HOME,
    VAR_CWD,
    VAR_TMP,
    VAR_INPUT_PATH,
    VAR_INPUT_NAMEEXT,
    VAR_INPUT_NAMENOEXT,
    VAR_INPUT_EXT,
    VAR_INPUT_PARENT_PATH,
    VAR_INPUT_PARENT_NAME,
]
VARIABLES_INPUT_BASED = {
    VAR_HOME: False,
    VAR_CWD: False,
    VAR_TMP: False,
    VAR_INPUT_PATH: True,
    VAR_INPUT_NAMEEXT: True,
    VAR_INPUT_NAMENOEXT: True,
    VAR_INPUT_EXT: True,
    VAR_INPUT_PARENT_PATH: True,
    VAR_INPUT_PARENT_NAME: True,
}
VARIABLES_LAMBDA = {
    VAR_HOME: lambda i: os.path.expanduser("~"),
    VAR_CWD: lambda i: os.getcwd(),
    VAR_TMP: lambda i: tempfile.gettempdir(),
    VAR_INPUT_PATH: lambda i: os.path.dirname(i),
    VAR_INPUT_NAMEEXT: lambda i: os.path.basename(i),
    VAR_INPUT_NAMENOEXT: lambda i: os.path.splitext(os.path.basename(i))[0],
    VAR_INPUT_EXT: lambda i: os.path.splitext(i)[1],
    VAR_INPUT_PARENT_PATH: lambda i: os.path.dirname(os.path.dirname(i)) if (len(os.path.dirname(i)) > 0) else "",
    VAR_INPUT_PARENT_NAME: lambda i: os.path.basename(os.path.dirname(i)) if (len(os.path.dirname(i)) > 0) else "",
}
VARIABLES_DESCRIPTION = {
    VAR_HOME: "The home directory of the current user.",
    VAR_CWD: "The current working directory.",
    VAR_TMP: "The temp directory.",
    VAR_INPUT_PATH: "The directory part of the current input, i.e., '/some/where' of input '/some/where/file.txt'.",
    VAR_INPUT_NAMEEXT: "The name (incl extension) of the current input, i.e., 'file.txt' of input '/some/where/file.txt'.",
    VAR_INPUT_NAMENOEXT: "The name (excl extension) of the current input, i.e., 'file' of input '/some/where/file.txt'.",
    VAR_INPUT_EXT: "The extension of the current input (incl dot), i.e., '.txt' of input '/some/where/file.txt'.",
    VAR_INPUT_PARENT_PATH: "The directory part of the parent directory of the current input, i.e., '/some' of input '/some/where/file.txt'.",
    VAR_INPUT_PARENT_NAME: "The name of the parent directory of the current input, i.e., 'where' of input '/some/where/file.txt'.",
}
USER_DEFINED_VARIABLES = set()


class VariableSupporter:
    """
    Indicator mixin whether a class supports variables in some form.
    Used for outputting help information.
    """
    pass


class InputBasedVariableSupporter(VariableSupporter):
    """
    Indicator mixin whether a class supports input-based variables.
    Used for outputting help information.
    """
    pass


def add_variable(variable: str, description: str, input_based: bool, lambda_func):
    """
    Allows adding a custom variable.

    :param variable: the variable itself
    :type variable: str
    :param description: the description for the variable, used in the variable_help() method
    :type description: str
    :param input_based: whether the variable relies on the current input
    :type input_based: str
    :param lambda_func: the lambda to use for expanding the variable, takes one argument: current input
    """
    if "{" not in variable:
        variable = "{" + variable + "}"
    if variable not in VARIABLES:
        VARIABLES.append(variable)
    VARIABLES_DESCRIPTION[variable] = description
    VARIABLES_INPUT_BASED[variable] = input_based
    VARIABLES_LAMBDA[variable] = lambda_func


def expand_variables(template: str, current_input: str = None) -> str:
    """
    Expands the variable in the template using the current input.

    :param current_input: the current input dir/file to use for the expansion
    :type current_input: str
    :param template: the template to expand
    :type template: str
    :return: the expanded string
    :rtype: str
    """
    result = template

    if "{" in result:
        for ph in VARIABLES:
            input_based = VARIABLES_INPUT_BASED[ph]
            lambda_func = VARIABLES_LAMBDA[ph]
            value = None
            if not input_based:
                value = lambda_func(None)
            elif input_based and (current_input is not None):
                value = lambda_func(current_input)
            if value is not None:
                result = result.replace(ph, value)

    return result


def variables(input_based: bool = False) -> List[str]:
    """
    Returns the variable names as list. Excludes user-defined variables.

    :param input_based: whether to include input based ones
    :type input_based: bool
    :return: the list of variables
    :rtype: list
    """
    result = []
    for ph in VARIABLES_INPUT_BASED:
        if ph in USER_DEFINED_VARIABLES:
            continue
        if input_based and VARIABLES_INPUT_BASED[ph]:
            result.append(ph)
        if not VARIABLES_INPUT_BASED[ph]:
            result.append(ph)
    return result


def variable_list(input_based: bool = False, obj=None) -> str:
    """
    Returns a short string of supported variables as list, e.g., to be used in the help string
    of argparse options, e.g.: variable_list(obj=self).

    :param input_based: whether to include input based ones
    :type input_based: bool
    :param obj: the object to determine the variable mixin from, overrides input_based parameter
    :return: the generated string
    :rtype: str
    """
    if obj is not None:
        input_based = isinstance(obj, InputBasedVariableSupporter)
    return "Supported variables: %s" % ", ".join(variables(input_based=input_based))


def variable_help(input_based: bool = False, obj=None, markdown: bool = False) -> str:
    """
    Returns help on variables.

    :param input_based: whether to include input based ones
    :type input_based: bool
    :param obj: the object to determine the variable mixin from, overrides input_based parameter
    :param markdown: whether to generate markdown or plain text
    :type markdown: bool
    :return: the generated help string
    :rtype: str
    """
    if obj is not None:
        input_based = isinstance(obj, InputBasedVariableSupporter)
    result = "Available variables:"
    if markdown:
        result += "\n"
    for ph in variables(input_based=input_based):
        if markdown:
            result += "\n* `" + ph + "`: " + VARIABLES_DESCRIPTION[ph].replace("'", "`")
        else:
            result += "\n- " + ph + ": " + VARIABLES_DESCRIPTION[ph]
    return result


def load_user_defined_variables(path: str):
    """
    Loads variables from the specified text file (format: key=value) that are not input-based.
    With "key" being the name of the variable without the curly brackets and value the path
    that it represents. Ignores empty lines or lines that start with '#' or ';'.

    :param path: the file with the variables to load
    :type path: str
    """
    with open(path, "r") as fp:
        lines = fp.readlines()
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        if line.startswith("#"):
            continue
        parts = line.split("=")
        if len(parts) == 2:
            ph = "{" + parts[0] + "}"
            USER_DEFINED_VARIABLES.add(ph)
            # we need early binding via the second parameter
            def f(ignored, r=parts[1]):
                return r
            add_variable(ph, "", False, f)
        else:
            print("Invalid variable format (key=value): %s" % line)
