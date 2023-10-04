import argparse

from typing import List


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
