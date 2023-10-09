import importlib
import inspect
import os
import sys
import traceback

from typing import List, Union, Optional, Dict
from pkg_resources import working_set

from ._plugin import Plugin
from ._types import get_class


MODE_EXPLICIT = "explicit"
MODE_DYNAMIC = "dynamic"
MODES = [
    MODE_EXPLICIT,
    MODE_DYNAMIC,
]


class Registry:
    """
    Registry for managing plugins derived from seppl.Plugin class.

    Entry points must have the format:

    1. explicit mode

    Each plugin has to be listed by (unique) name ("plugin_name"), with the
    module it resides in ("plugin_module") and its class name ("plugin_class"):

    entry_points={
        "group": [
            "plugin_name=plugin_module:plugin_class",
        ]
    }

    2. dynamic mode

    Only the superclass is listed

    entry_points={
        "group": [
            "unique_string=plugin_module:superclass_name",
        ]
    }

    If a super class ("superclass_name1") has classes in multiple modules
    ("plugin_module1", "plugin_module2"), then these modules need to be
    listed separately:

    entry_points={
        "group": [
            "unique_string1=plugin_module1:superclass_name1",
            "unique_string2=plugin_module2:superclass_name1",
            "unique_string3=plugin_module3:superclass_name2",
            ...
        ]
    }

    When enforcing uniqueness, the "plugin_name" must be unique across all plugins.
    """

    def __init__(self, mode: Optional[str] = MODE_EXPLICIT,
                 default_modules: Optional[Union[str, List[str]]] = None,
                 env_modules: Optional[str] = None,
                 enforce_uniqueness: bool = True):
        """
        Initializes the registry. default_modules and env_modules are used as fallback option
        in case no plugins are being obtained from entry_points.

        :param mode: how the registry parses the entry_points
        :type mode: str
        :param default_modules: the default modules to use for registering plugins, comma-separated string of module names or list of module names, ignored if None
        :type default_modules: str or list
        :param env_modules: the environment variable to retrieve the modules from (overrides default ones)
        :type env_modules: str
        :param enforce_uniqueness: whether plugin names must be unique
        :type enforce_uniqueness: bool
        """
        if mode not in MODES:
            raise Exception("Unknown mode: %s" % mode)

        self._plugins = dict()
        self._all_plugins = dict()
        self._custom_modules = None
        self._default_modules = None
        self._env_modules = None

        self.mode = mode
        self.default_modules = default_modules
        self.env_modules = env_modules
        self.enforce_uniqueness = enforce_uniqueness

    def _has_env_modules(self) -> bool:
        """
        Checks whether an environment variable for modules is set.

        :return: True if set
        :rtype: bool
        """
        return (self._env_modules is not None) \
               and (len(self._env_modules) > 0) \
               and (os.getenv(self._env_modules) is not None) \
               and (len(os.getenv(self._env_modules)) > 0)

    @property
    def default_modules(self) -> Optional[List[str]]:
        """
        Returns the default modules.

        :return: the modules
        :rtype: list
        """
        return self._default_modules

    @default_modules.setter
    def default_modules(self, modules: Optional[Union[str, List[str]]]):
        """
        Sets/unsets the default modules to use. Clears the plugin cache.

        :param modules: the list of modules to use, None to unset
        :type modules: list
        """
        if modules is None:
            modules = ""
        if isinstance(modules, str):
            modules = [x.strip() for x in modules.split(",")]
        elif isinstance(modules, list):
            modules = modules[:]
        else:
            raise Exception("default_modules must be either str or list, but got: %s" % str(type(modules)))
        if len(modules) == 0:
            raise Exception("No default modules defined!")
        self._default_modules = modules
        self._plugins = dict()

    @property
    def env_modules(self) -> Optional[str]:
        """
        Returns the environment modules (if any).

        :return: the modules, None if none set
        :rtype: str
        """
        return self._env_modules

    @env_modules.setter
    def env_modules(self, modules: Optional[str]):
        """
        Sets/unsets the environment variable with the modules to use. Clears the plugin cache.

        :param modules: the environment variable with the modules to use, None to unset
        :type modules: str
        """
        self._env_modules = modules
        self._plugins = dict()

    @property
    def custom_modules(self) -> Optional[List[str]]:
        """
        Returns the custom modules (if any).

        :return: the modules, None if none set
        :rtype: list
        """
        return self._custom_modules

    @custom_modules.setter
    def custom_modules(self, modules: Optional[Union[str, List[str]]]):
        """
        Sets/unsets the custom modules to use. Clears the plugin cache.

        :param modules: the list of modules to use, None to unset
        :type modules: list
        """
        self._custom_modules = modules
        self._plugins = dict()

    def _get_modules(self) -> List[str]:
        """
        Returns list the of modules to fall back on.
        Precedence: custom_modules > env_modules > default_modules

        :return: the list of modules
        :rtype: list
        """
        if (self._custom_modules is not None) and (len(self._custom_modules) > 0):
            return self._custom_modules

        if self._has_env_modules():
            return [x.strip() for x in os.getenv(self.env_modules).split(",")]

        return self.default_modules[:]

    def _register_plugin(self, d: Dict[str, Plugin], o: Plugin):
        """
        Adds the plugin to the registry dictionary under its name.
        Ensures that names are unique and throws an Exception if not.

        :param d: the dictionary to add the handler to
        :type d: dict
        :param o: the plugin to register
        :type o: CommandlineHandler
        """
        if self.enforce_uniqueness and (o.name() in self._all_plugins):
            raise Exception("Duplicate plugin name encountered: name=%s, existing type=%s, new type=%s)"
                            % (o.name(), str(type(self._all_plugins[o.name()])), str(type(o))))
        else:
            self._all_plugins[o.name()] = o
            d[o.name()] = o

    def _init_plugin_class(self, c):
        """
        Initializes the class to restrict the plugins to.

        :param c: the class, uses Plugin if None
        :return: the plugin class
        """
        if c is None:
            c = Plugin
        elif not issubclass(c, Plugin):
            raise Exception("Class '%s' is not derived from '%s'!" % (str(c), str(Plugin)))
        return c

    def _register_from_module(self, m: str, c: Optional = None):
        """
        Locates all the classes implementing the specified class in the module and
        adds them to the dictionary.

        :param m: the module to look for classes
        :type m: str
        :param c: the class that the plugins must be, any class derived from Plugin if None
        """
        c = self._init_plugin_class(c)
        result = dict()

        module = importlib.import_module(m)
        for att_name in dir(module):
            if att_name.startswith("_"):
                continue
            att = getattr(module, att_name)
            if inspect.isclass(att) and issubclass(att, c):
                try:
                    p = att()
                    self._register_plugin(result, p)
                    result[p.name()] = p
                except NotImplementedError:
                    pass
                except:
                    print("Problem encountered instantiating: " + m + "." + att_name, file=sys.stderr)
                    traceback.print_exc()

        return result

    def _register_from_modules(self, c: Optional = None):
        """
        Locates all the classes implementing the specified class and adds them to the dictionary.

        :param c: the class that the plugins must be, any class derived from Plugin if None
        """
        c = self._init_plugin_class(c)
        result = dict()

        for m in self._get_modules():
            result.update(self._register_from_module(m, c))

        return result

    def _register_from_entry_point(self, group: str, c: Optional = None) -> Dict[str, Plugin]:
        """
        Generates a dictionary (name/object) for the specified entry_point group.

        :param group: the entry_point group to generate dictionary for
        :type group: str
        :return: the generated dictionary
        :rtype: dict
        """
        c = self._init_plugin_class(c)
        result = dict()

        for item in working_set.iter_entry_points(group, None):
            # format: "plugin_name=plugin_module:plugin_class",
            if self.mode == MODE_EXPLICIT:
                cls = get_class(module_name=item.module_name, class_name=item.attrs[0])
                if issubclass(cls, c):
                    p = cls()
                    self._register_plugin(result, p)
                    result[p.name()] = p
            # format: "unique_string=plugin_module:superclass_name",
            elif self.mode == MODE_DYNAMIC:
                c = get_class(full_class_name=".".join(item.attrs))
                result.update(self._register_from_module(item.module_name, c))
            else:
                raise Exception("Unhandled mode: %s" % self.mode)

        return result

    def _register(self, group: str, c: Optional = None):
        """
        Registers all plugins that match the specified class.

        :param group: the entry point group to get the plugins from
        :type group: str
        :param c: the class that the plugins must be, any class derived from Plugin if None
        """
        c = self._init_plugin_class(c)

        # from entry points
        plugins = self._register_from_entry_point(group, c=c)

        # fall back on modules?
        if len(plugins) == 0:
            plugins = self._register_from_modules(c=c)

        self._plugins[group] = plugins

    def plugins(self, group: str, c: Optional = None) -> Dict[str, Plugin]:
        """
        Returns the plugins for the specified class.

        :param group: the entry point group to get the plugins for
        :type group: str
        :param c: the class that the plugins must be, any class derived from Plugin if None
        :return: the dictionary of plugins (name / plugin association)
        :rtype: dict
        """
        if group not in self._plugins:
            self._register(group, c)
        return self._plugins[group]
