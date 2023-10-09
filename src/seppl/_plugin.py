import argparse

from typing import List
from ._types import classes_to_str


class Plugin:
    """
    Base class for plugins.
    """

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        raise NotImplementedError()

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        raise NotImplementedError()

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = argparse.ArgumentParser(
            description=self.description(),
            prog=self.name(),
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        pass

    def parse_args(self, args: List[str]) -> 'Plugin':
        """
        Parses the command-line arguments.

        :param args: the arguments to parse
        :type args: list
        :return: itself
        :rtype: Plugin
        """
        parser = self._create_argparser()
        self._apply_args(parser.parse_args(args))
        return self

    def print_help(self):
        """
        Outputs the help in the console.
        """
        self._create_argparser().print_help()

    def format_help(self) -> str:
        """
        Returns the formatted help string.

        :return: the help string
        :rtype: str
        """
        return self._create_argparser().format_help()


class OutputProducer(object):
    """
    Mixin for classes that generate output.
    """

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        raise NotImplementedError()


class InputConsumer(object):
    """
    Mixin for classes that consume input.
    """

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        raise NotImplementedError()


def check_compatibility(plugins: List[Plugin]):
    """
    Checks whether the plugins are compatible based on their inputs/outputs.
    Raises an exception if not compatible.

    :param plugins: the list of plugins to check
    :type plugins: list
    """
    if len(plugins) == 0:
        return

    for i in range(len(plugins) - 1):
        plugin1 = plugins[i]
        plugin2 = plugins[i + 1]
        index1 = "#" + str(i)
        index2 = "#" + str(i+1)
        if not isinstance(plugin1, OutputProducer):
            raise Exception(index1 + "/" + plugin1.name() + " is not an OutputProducer!")
        if not isinstance(plugin2, InputConsumer):
            raise Exception(index2 + "/" + plugin2.name() + " is not an InputConsumer!")
        classes1 = plugin1.generates()
        classes2 = plugin2.accepts()
        compatible = False
        for class1 in classes1:
            if class1 in classes2:
                compatible = True
                break
        if not compatible:
            raise Exception(
                "Output(s) of " + index1 + "/" + plugin1.name()
                + " not compatible with input(s) of " + index2 + "/" + plugin2.name() + ": "
                + classes_to_str(classes1) + " != " + classes_to_str(classes2))
