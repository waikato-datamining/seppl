import os

PH_INPUT_PATH = "{INPUT_PATH}"
PH_INPUT_NAMEEXT = "{INPUT_NAMEEXT}"
PH_INPUT_NAMENOEXT = "{INPUT_NAMENOEXT}"
PH_INPUT_EXT = "{INPUT_EXT}"
PH_INPUT_PARENT_PATH = "{INPUT_PARENT_PATH}"
PH_INPUT_PARENT_NAME = "{INPUT_PARENT_NAME}"
PLACEHOLDERS = [
    PH_INPUT_PATH,
    PH_INPUT_NAMEEXT,
    PH_INPUT_NAMENOEXT,
    PH_INPUT_EXT,
    PH_INPUT_PARENT_PATH,
    PH_INPUT_PARENT_NAME,
]
PLACEHOLDERS_HELP = {
    PH_INPUT_PATH: "The directory part of the current input, i.e., '/some/where' of input '/some/where/file.txt'.",
    PH_INPUT_NAMEEXT: "The name (incl extension) of the current input, i.e., 'file.txt' of input '/some/where/file.txt'.",
    PH_INPUT_NAMENOEXT: "The name (excl extension) of the current input, i.e., 'file' of input '/some/where/file.txt'.",
    PH_INPUT_EXT: "The extension of the current input (incl dot), i.e., '.txt' of input '/some/where/file.txt'.",
    PH_INPUT_PARENT_PATH: "The directory part of the parent directory of the current input, i.e., '/some' of input '/some/where/file.txt'.",
    PH_INPUT_PARENT_NAME: "The name of the parent directory of the current input, i.e., 'where' of input '/some/where/file.txt'.",
}


def expand_placeholders(current_input: str, template: str) -> str:
    """
    Expands the placeholder in the template using the current input.

    :param current_input: the current input dir/file to use for the expansion
    :type current_input: str
    :param template: the template to expand
    :type template: str
    :return: the expanded string
    :rtype: str
    """
    result = template

    if (current_input is not None) and ("{" in result):
        for ph in PLACEHOLDERS:
            if ph in result:
                dir_name = os.path.dirname(current_input)
                value = None
                if dir_name is None:
                    dir_name = ""
                if ph == PH_INPUT_PATH:
                    value = dir_name
                elif ph == PH_INPUT_NAMEEXT:
                    value = os.path.basename(current_input)
                elif ph == PH_INPUT_NAMENOEXT:
                    value = os.path.splitext(os.path.basename(current_input))[0]
                elif ph == PH_INPUT_EXT:
                    value = os.path.splitext(os.path.basename(current_input))[1]
                elif ph == PH_INPUT_PARENT_PATH:
                    if len(dir_name) > 0:
                        value = os.path.dirname(dir_name)
                elif ph == PH_INPUT_PARENT_NAME:
                    if len(dir_name) > 0:
                        value = os.path.basename(dir_name)
                else:
                    print("Unhandled placeholder: %s" % ph)
                if value is not None:
                    result = result.replace(ph, value)

    return result


def placeholder_help(short: bool = True, markdown: bool = False) -> str:
    """
    Returns help on placeholders.

    :param short: whether to return a short help string, e.g., for option help strings.
    :type short: bool
    :param markdown: whether to generate markdown or plain text
    :type markdown: bool
    :return: the generated help string
    :rtype: str
    """
    if short:
        result = "Supported placeholders: %s" % ", ".join(PLACEHOLDERS)
    else:
        result = "Available placeholders:"
        if markdown:
            result += "\n"
        for ph in PLACEHOLDERS:
            if markdown:
                result += "\n* `" + ph + "`: " + PLACEHOLDERS_HELP[ph].replace("'", "`")
            else:
                result += "\n- " + ph + ": " + PLACEHOLDERS_HELP[ph]
    return result


class PlaceholderSupporter:
    """
    Indicator mixin whether a class supports placeholders in some form.
    Used for outputting help information.
    """
    pass
