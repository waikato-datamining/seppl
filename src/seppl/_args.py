import copy
import shlex

from typing import List, Dict, Tuple, Iterable, Set, Optional
from ._plugin import Plugin, SkippablePlugin


def escape_args(args: List[str]) -> List[str]:
    """
    Escapes any unicode characters in the arguments.

    :param args: the arguments to process
    :type args: list
    :return: the (potentially) updated arguments
    :rtype: list
    """
    result = []
    for arg in args:
        result.append(arg.encode("unicode_escape").decode())
    return result


def unescape_args(args: List[str]) -> List[str]:
    """
    Unescapes unicode characters in the arguments.

    :param args: the arguments to process
    :type args: list
    :return: the (potentially) updated arguments
    :rtype: list
    """
    result = []
    for arg in args:
        result.append(arg.encode().decode("unicode_escape"))
    return result


def split_cmdline(cmdline: str, unescape: bool = False) -> List[str]:
    """
    Splits the command-line into arguments.

    :param cmdline: the commandline to split
    :type cmdline: str
    :param unescape: whether to unescape unicode chars
    :type unescape: bool
    :return: the list of arguments
    :rtype: list
    """
    result = shlex.split(cmdline)
    if unescape:
        result = unescape_args(result)
    return result


def resolve_handler(search: str, handlers: Set[str], partial: bool = False) -> Optional[str]:
    """
    Tries to find the "search" string among the handlers, exact and partial match.

    :param search: the potential handler to find
    :type search: str
    :param handlers: the set of valid handlers to match against
    :type handlers: set
    :param partial: whether to allow partial matches
    :type partial: bool
    :return: the match or None if failed to find
    :rtype: str or None
    """
    # exact match?
    if search in handlers:
        return search

    if partial:
        # unique partial match?
        matches = []
        for handler in handlers:
            if handler.startswith(search):
                matches.append(handler)
        if len(matches) == 1:
            return matches[0]

    # nothing found
    return None


def split_args(args: List[str], handlers: List[str], unescape: bool = False, partial: bool = False) -> Dict[str, List[str]]:
    """
    Splits the command-line arguments into handler and their associated arguments.
    Special entry "" is used for global options.

    :param args: the command-line arguments to split
    :type args: list
    :param handlers: the list of valid handler names
    :type handlers: list
    :param unescape: whether to unescape unicode chars
    :type unescape: bool
    :param partial: whether to allow partial matches (may interfer with options, so use carefully)
    :type partial: bool
    :return: the dictionary for handler index / handler name + options list
    :rtype: dict
    """
    handlers_set = set(handlers)
    result = dict()
    last_handler = ""
    last_args = []

    if unescape:
        args = unescape_args(args)

    for arg in args:
        handler = resolve_handler(arg, handlers_set, partial=partial)
        if handler is not None:
            if len(last_handler) > 0:
                result[str(len(result))] = last_args
            else:
                result[""] = last_args
            last_handler = handler
            last_args = [handler]
            continue
        else:
            last_args.append(arg)

    if len(last_args) > 0:
        result[str(len(result))] = last_args

    return result


def args_to_objects(args: Dict[str, List[str]], valid_plugins: Dict[str, Plugin], allow_global_options: bool = False, allow_unknown_args: bool = False, unescape: bool = False) -> List[Plugin]:
    """
    Instantiates the plugins from the parsed arguments dictionary.
    Automatically removes SkippablePlugin instances that are to be skipped.

    :param args: the arguments dictionary generated by split_args
    :type args: dict
    :param valid_plugins: the dictionary of valid plugins to use as templates
    :type valid_plugins: dict
    :param allow_global_options: whether global options are allowed (ie options that don't follow a plugin name)
    :type allow_global_options: bool
    :param allow_unknown_args: whether to allow unknown args (eg typos or unknown plugins)
    :type allow_unknown_args: bool
    :param unescape: whether to unescape unicode chars
    :type unescape: bool
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
        sub_args = args[key][1:]
        if unescape:
            sub_args = unescape_args(sub_args)
        unknown = plugin.parse_args(sub_args)
        if not allow_unknown_args and (len(unknown) > 0):
            raise Exception("Found unknown argument(s) for plugin '%s': %s" % (plugin.name(), str(unknown)))
        result.append(plugin)

    # remove plugins to be skipped
    i = 0
    while i < len(result):
        try:
            if isinstance(result[i], SkippablePlugin) and result[i].is_skipped:
                result.pop(i)
                continue
        except:
            pass
        i += 1

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


def enumerate_plugins(plugins: Iterable[str], aliases: List[str] = None, alias_flag: str = "*", prefix: str = "", width: int = 72) -> str:
    """
    Turns the list of plugin names into a string.

    :param plugins: the plugin names to turn into a string
    :type plugins: Iterable
    :param aliases: the list of known aliases (for flagging them in the generated list)
    :type aliases: list
    :param alias_flag: the string to use for identifying aliases
    :type alias_flag: str
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
        if aliases is not None:
            if plugin in aliases:
                line += alias_flag

    if len(line) > 0:
        result.append(line)
    return "\n".join(result)
