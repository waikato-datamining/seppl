import importlib
import inspect

from typing import Optional


def get_class(full_class_name: Optional[str] = None,
              module_name: Optional[str] = None, class_name: Optional[str] = None) -> type:
    """
    Returns the class object associated with the dot-notation classname.
    Either the fully qualified class name or module and class name can be supplied.

    :param full_class_name: the classname (module + name)
    :type full_class_name: str
    :param module_name: the name of the module
    :type module_name: str
    :param class_name: the
    :return: the class object
    """
    if full_class_name is not None:
        parts = full_class_name.split('.')
        module = ".".join(parts[:-1])
        m = importlib.import_module(module)
        c = getattr(m, parts[-1])
        return c
    elif (module_name is not None) and (class_name is not None):
        m = importlib.import_module(module_name)
        c = getattr(m, class_name)
        return c
    else:
        raise Exception("Either fully qualified class name or module and class name must be supplied!")


def get_class_name(obj: object) -> str:
    """
    Returns the fully qualified classname of the Python class or object.

    :param obj: the Python class/object to get the classname for
    :type obj: object
    :return: the generated classname
    :rtype: str
    """
    if inspect.isclass(obj):
        return obj.__module__ + "." + obj.__name__
    else:
        return get_class_name(obj.__class__)
