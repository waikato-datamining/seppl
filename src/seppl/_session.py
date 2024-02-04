import argparse
import logging

from dataclasses import dataclass

from wai.logging import set_logging_level


@dataclass
class Session:
    """
    Session object shared among reader, filter(s), writer.
    """
    options: argparse.Namespace = None
    """ global options. """

    logger: logging.Logger = None
    """ the global logger. """

    count: int = 0
    """ the record counter. """

    current_input = None
    """ the current input etc. """

    def _add_option(self, name: str, value):
        """
        Adds the key/value to the global options.

        :param name: the name of the option
        :type name: str
        :param value: the value of the option
        """
        if self.options is None:
            self.options = argparse.Namespace()
        setattr(self.options, name, value)

    def set_logging_level(self, level: str):
        """
        Sets the global logging level.

        :param level: the level
        :type level: str
        :return: itself
        :rtype: Session
        """
        self._add_option("logging_level", level)
        set_logging_level(self.logger, level)
        return self


class SessionHandler(object):
    """
    Mixin for classes that support session objects.
    """

    @property
    def session(self) -> Session:
        """
        Returns the current session object

        :return: the session object
        :rtype: Session
        """
        raise NotImplementedError()

    @session.setter
    def session(self, s: Session):
        """
        Sets the session object to use.

        :param s: the session object
        :type s: Session
        """
        raise NotImplementedError()
