import importlib
import inspect
import os
import sys
import traceback

from typing import List, Union, Optional, Dict
from pkg_resources import working_set

from ._plugin import Plugin


class Registry:
    """
    Registry for managing plugins that are identified by their names.
    """

    def __init__(self, default_modules: Optional[Union[str, List[str]]] = None,
                 env_modules: Optional[str] = None,
                 enforce_uniqueness: bool = True):
        """
        Initializes the registry. default_modules and env_modules are used as fallback option
        in case no plugins are being obtained from entry_points.

        :param default_modules: the default modules to use for registering plugins, comma-separated string of module names or list of module names, ignored if None
        :type default_modules: str or list
        :param env_modules: the environment variable to retrieve the modules from (overrides default ones)
        :type env_modules: str
        :param enforce_uniqueness: whether plugin names must be unique
        :type enforce_uniqueness: bool
        """
        self._plugins = dict()
        self._all_plugins = dict()
        self._custom_modules = None
        self._default_modules = None
        self._env_modules = None

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

    def _register_from_entry_point(self, group: str, c: Optional = None) -> Dict[str, Plugin]:
        """
        Generates a dictionary (name/object) for the specified entry_point group.

        :param group: the entry_point group to generate dictionary for
        :type group: str
        :return: the generated dictionary
        :rtype: dict
        """
        if c is None:
            c = Plugin
        result = dict()
        for item in working_set.iter_entry_points(group, None):
            module = importlib.import_module(item.module_name)
            cls = getattr(module, item.attrs[0])
            if issubclass(cls, c):
                self._register_plugin(result, cls())
        return result

    def _register_from_modules(self, c: Optional = None):
        """
        Locates all the classes implementing the specified class and adds them to the dictionary.

        :param c: the class that the plugins must be, any class derived from Plugin if None
        """
        if c is None:
            c = Plugin
        elif not issubclass(c, Plugin):
            raise Exception("Class '%s' is not derived from '%s'!" % (str(c), str(Plugin)))

        result = dict()

        for m in self._get_modules():
            module = importlib.import_module(m)
            for att in dir(module):
                if att.startswith("_"):
                    continue
                cls = getattr(module, att)
                if inspect.isclass(cls) and issubclass(cls, c):
                    try:
                        self._register_plugin(result, cls())
                    except NotImplementedError:
                        pass
                    except:
                        print("Problem encountered instantiating: " + m + "." + att, file=sys.stderr)
                        traceback.print_exc()

        return result

    def _register(self, group: str, c: Optional = None):
        """
        Registers all plugins that match the specified class.

        :param group: the entry point group to get the plugins from
        :type group: str
        :param c: the class that the plugins must be, any class derived from Plugin if None
        """
        if c is None:
            c = Plugin
        elif not issubclass(c, Plugin):
            raise Exception("Class '%s' is not derived from '%s'!" % (str(c), str(Plugin)))

        # from entry points
        plugins = self._register_from_entry_point(group, c=c)

        # fall back on modules?
        if len(plugins) == 0:
            plugins = self._register_from_modules(c=c)

        self._plugins[group] = plugins

    def plugins(self, group: str, c: Optional = None) -> Dict[str, Plugin]:
        """
        Returns the plugins for the specified class.

        Entry points must have the format:

        entry_points={
            "group": [
                "plugin_name=plugin_module:plugin_class",
            ]
        }
        
        When enforcing uniqueness, the "plugin_name" must be unique across all plugins.

        :param group: the entry point group to get the plugins for
        :type group: str
        :param c: the class that the plugins must be, any class derived from Plugin if None
        :return: the dictionary of plugins (name / plugin association)
        :rtype: dict
        """
        if group not in self._plugins:
            self._register(group, c)
        return self._plugins[group]
