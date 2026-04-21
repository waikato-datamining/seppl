from seppl.variables import VariableSupporter, InputBasedVariableSupporter
from seppl.variables import add_variable, expand_variables, variable_list, variable_help, load_user_defined_variables


PlaceholderSupporter = VariableSupporter


InputBasedPlaceholderSupporter = InputBasedVariableSupporter


def add_placeholder(placeholder: str, description: str, input_based: bool, lambda_func):
    """
    DEPRECATED - use seppl.variables.add_variable instead

    Allows adding a custom placeholder.

    :param placeholder: the placeholder itself
    :type placeholder: str
    :param description: the description for the placeholder, used in the placeholder_help() method
    :type description: str
    :param input_based: whether the placeholder relies on the current input
    :type input_based: str
    :param lambda_func: the lambda to use for expanding the placeholder, takes one argument: current input
    """
    add_variable(placeholder, description, input_based, lambda_func)


def expand_placeholders(template: str, current_input: str = None) -> str:
    """
    DEPRECATED - use seppl.variables.expand_variables instead

    Expands the placeholder in the template using the current input.

    :param current_input: the current input dir/file to use for the expansion
    :type current_input: str
    :param template: the template to expand
    :type template: str
    :return: the expanded string
    :rtype: str
    """
    return expand_variables(template, current_input)


def placeholder_list(input_based: bool = False, obj=None) -> str:
    """
    DEPRECATED - use seppl.variables.variable_list instead

    Returns a short string of supported placeholders as list, e.g., to be used in the help string
    of argparse options, e.g.: placeholder_list(obj=self).

    :param input_based: whether to include input based ones
    :type input_based: bool
    :param obj: the object to determine the placeholder mixin from, overrides input_based parameter
    :return: the generated string
    :rtype: str
    """
    return variable_list(input_based, obj=obj)


def placeholder_help(input_based: bool = False, obj=None, markdown: bool = False) -> str:
    """
    DEPRECATED - use seppl.variables.variable_help instead

    Returns help on placeholders.

    :param input_based: whether to include input based ones
    :type input_based: bool
    :param obj: the object to determine the placeholder mixin from, overrides input_based parameter
    :param markdown: whether to generate markdown or plain text
    :type markdown: bool
    :return: the generated help string
    :rtype: str
    """
    return variable_help(input_based, obj=obj, markdown=markdown)


def load_user_defined_placeholders(path: str):
    """
    DEPRECATED - use seppl.variables.load_user_defined_variables instead

    Loads placeholders from the specified text file (format: key=value) that are not input-based.
    With "key" being the name of the placeholder without the curly brackets and value the path
    that it represents. Ignores empty lines or lines that start with '#' or ';'.

    :param path: the file with the placeholders to load
    :type path: str
    """
    return load_user_defined_variables(path)
