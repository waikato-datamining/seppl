import copy
import shlex

from typing import List, Dict, Tuple, Iterable
from ._plugin import Plugin


def split_cmdline(cmdline: str) -> List[str]:
    """
    Splits the command-line into arguments.

    :param cmdline: the commandline to split
    :type cmdline: str
    :return: the list of arguments
    :rtype: list
    """
    return shlex.split(cmdline)


def split_args(args: List[str], handlers: List[str]) -> Dict[str, List[str]]:
    """
    Splits the command-line arguments into handler and their associated arguments.
    Special entry "" is used for global options.

    :param args: the command-line arguments to split
    :type args: list
    :param handlers: the list of valid handler names
    :type handlers: list
    :return: the dictionary for handler index / handler name + options list
    :rtype: dict
    """
    handlers = set(handlers)
    result = dict()
    last_handler = ""
    last_args = []

    for arg in args:
        if arg in handlers:
            if len(last_handler) > 0:
                result[str(len(result))] = last_args
            else:
                result[""] = last_args
            last_handler = arg
            last_args = [arg]
            continue
        else:
            last_args.append(arg)

    if len(last_args) > 0:
        result[str(len(result))] = last_args

    return result


def args_to_objects(args: Dict[str, List[str]], valid_plugins: Dict[str, Plugin], allow_global_options: bool = False) -> List[Plugin]:
    """
    Instantiates the plugins from the parsed arguments dictionary.

    :param args: the arguments dictionary generated by split_args
    :type args: dict
    :param valid_plugins: the dictionary of valid plugins to use as templates
    :type valid_plugins: dict
    :param allow_global_options: whether global options are allowed (ie options that don't follow a plugin name)
    :type allow_global_options: bool
    :return: the list of instantiated plugins
    :rtype: list
    """
    result = []
    for key in args:
        if key == "":
            if (not allow_global_options) and (len(args[""]) > 0):
                raise Exception("No global options allowed (found: %s)!" % str(args[""]))
            else:
                continue

        name = args[key][0]
        plugin = copy.deepcopy(valid_plugins[name])
        plugin.parse_args(args[key][1:])
        result.append(plugin)
    return result


def is_help_requested(args: List[str]) -> Tuple[bool, bool, str]:
    """
    Checks whether help was requested.

    :param args: the arguments to check
    :type args: list
    :return: the tuple of help requested: (help_requested, plugin_details, plugin_name)
    :rtype: tuple
    """
    help_requested = False
    plugin_details = False
    plugin_name = None
    for index, arg in enumerate(args):
        if (arg == "-h") or (arg == "--help"):
            help_requested = True
            break
        if arg == "--help-all":
            help_requested = True
            plugin_details = True
            break
        if arg == "--help-plugin":
            help_requested = True
            if index < len(args) - 1:
                plugin_name = args[index + 1]
            break
    return help_requested, plugin_details, plugin_name


def enumerate_plugins(plugins: Iterable[str], prefix: str = "", width: int = 72) -> str:
    """
    Turns the list of plugin names into a string.

    :param plugins: the plugin names to turn into a string
    :type plugins: Iterable
    :param prefix: the prefix string to use for each line
    :type prefix: str
    :param width: the maximum width of the string before adding a newline
    :type width: int
    :return: the generated string
    :rtype: str
    """
    result = []
    line = prefix
    for plugin in sorted(plugins):
        if (len(line) > 0) and (line[-1] != " "):
            line += ", "
        if len(line) + len(plugin) >= width:
            result.append(line)
            line = prefix + plugin
        else:
            line += plugin
    if len(line) > 0:
        result.append(line)
    return "\n".join(result)
