import abc
import argparse
import types
from typing import List, Any, Optional, Union

from wai.logging import LOGGING_WARNING

from seppl import InputConsumer, OutputProducer, PluginWithLogging, Initializable, Session, SessionHandler, \
    SkippablePlugin, add_skip_option, init_initializable

FILTER_ACTION_KEEP = "keep"
FILTER_ACTION_DISCARD = "discard"
FILTER_ACTIONS = [FILTER_ACTION_KEEP, FILTER_ACTION_DISCARD]


class BatchFilter(PluginWithLogging, InputConsumer, OutputProducer, SessionHandler, Initializable, SkippablePlugin, abc.ABC):
    """
    Base class for filters. Processes data in batches.
    """

    def __init__(self, logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the handler.

        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self._session = None
        self._last_input = None
        self.skip = False

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        add_skip_option(parser)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.skip = ns.skip

    @property
    def is_skipped(self) -> bool:
        """
        Returns whether the plugin is to be skipped.

        :return: True if to be skipped
        :rtype: bool
        """
        return self.skip

    @property
    def session(self) -> Session:
        """
        Returns the current session object

        :return: the session object
        :rtype: Session
        """
        return self._session

    @session.setter
    def session(self, s: Session):
        """
        Sets the session object to use.

        :param s: the session object
        :type s: Session
        """
        self._session = s

    def _has_input_changed(self, current_input: str = None, update: bool = False) -> bool:
        """
        Checks whether the current input is different from the last one we processed.

        :param current_input: the current input, uses the current_input from the session if None
        :type current_input: str
        :param update: whether to update the last input immediately
        :type update: bool
        :return: True if input has changed
        :rtype: bool
        """
        if current_input is None:
            current_input = self.session.current_input
        result = self._last_input != current_input
        if update:
            self._update_last_input(current_input)
        return result

    def _update_last_input(self, current_input: str):
        """
        Updates the last input that was processed.

        :param current_input: the "new" last input
        :type current_input: str
        """
        self._last_input = current_input

    def _requires_list_input(self) -> bool:
        """
        Returns whether lists are expected as input for the _process method.

        :return: True if list inputs are expected by the filter
        :rtype: bool
        """
        return False

    @abc.abstractmethod
    def _do_process(self, data):
        """
        Processes the data record(s).

        :param data: the record(s) to process
        :return: the potentially updated record(s)
        """
        raise NotImplementedError()

    def process(self, data):
        """
        Processes the data record.

        :param data: the record(s) to process
        :return: the potentially updated record or None if to drop
        """
        if self.skip:
            return data

        if isinstance(data, list):
            if self._requires_list_input():
                result = self._do_process(data)
            else:
                result = []
                for d in data:
                    r = self._do_process(d)
                    if r is not None:
                        if isinstance(r, list):
                            result.extend(r)
                        else:
                            result.append(r)
                if len(result) == 1:
                    result = result[0]
        else:
            if self._requires_list_input():
                result = self._do_process([data])
            else:
                result = self._do_process(data)
        return result


class StreamFilter(BatchFilter, abc.ABC):
    """
    Ancestor for streaming filters. May produce more output items than are being input.
    """

    def __init__(self, logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the handler.

        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self._stream_output = []

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        self._stream_output = []

    @abc.abstractmethod
    def _do_process_stream(self, data):
        """
        Filters the data.

        :param data: the data to filter
        """
        raise NotImplementedError()

    def process_stream(self, data):
        """
        Filters the data.

        :param data: the data to filter
        """
        self._stream_output = []
        if self.skip:
            self._stream_output.append(data)
        else:
            self._do_process_stream(data)

    def has_output(self) -> bool:
        """
        Whether any output is available.

        :return: True if output can be collected
        :rtype: bool
        """
        return len(self._stream_output) > 0

    def output(self) -> Optional[Any]:
        """
        Returns the next available output.

        :return: the output, None if nothing to return
        """
        if len(self._stream_output) > 0:
            return self._stream_output.pop(0)
        else:
            return None

    def finalize(self):
        """
        Finishes the processing, e.g., for closing files or databases.
        """
        super().finalize()
        self._stream_output = []


class FilterPipelineIterator:
    """
    Iterator for filtering data with zero or more filters efficiently.
    """

    def __init__(self, data: Any, filters: Optional[Union[BatchFilter, List[BatchFilter]]], session: Optional[Session] = None):
        """
        Initializes the filter iterator.

        :param data: the data to filter through the filters
        :param filters: the filter or list of filters to apply sequentially, can be None
        :type filters: Filter or list
        :param session: the optional session object for monitoring the stopped flag
        :type session: Session
        """
        self.data = data
        if filters is None:
            self.filters = []
        elif isinstance(filters, BatchFilter):
            self.filters = [filters]
        else:
            self.filters = filters
        self.session = session
        self.finished = False
        self.pending_filters = []
        self.first = True

    def __iter__(self):
        """
        Returns itself.

        :return: itself
        :rtype: FilterPipelineIterator
        """
        return self

    def __next__(self):
        """
        Returns the next filtered data that the filter pipeline generates.

        :return: the filtered data
        """
        # finished iterating?
        if self.finished:
            raise StopIteration()

        # nothing to do?
        if self.first:
            if (self.filters is None) or (len(self.filters) == 0):
                self.first = False
                self.finished = True
                return self.data

        while not self.finished:
            if (self.session is not None) and self.session.stopped:
                break

            # determine starting point of next iteration
            if len(self.pending_filters) > 0:
                start_index = self.filters.index(self.pending_filters[-1])
            else:
                start_index = 0

            # iterate over filters
            if self.first:
                output = self.data
                self.first = False
            else:
                output = None

            for i in range(start_index, len(self.filters)):
                if (self.session is not None) and self.session.stopped:
                    break

                curr = self.filters[i]

                if output is None:
                    if isinstance(curr, StreamFilter) and curr.has_output():
                        if len(self.pending_filters) > 0:
                            self.pending_filters.pop()
                        output = curr.output()
                        if curr.has_output():
                            self.pending_filters.append(curr)
                        # last filter? -> return value
                        if (i == len(self.filters) - 1) and (output is not None):
                            return output
                        else:
                            continue

                else:
                    if isinstance(curr, StreamFilter):
                        curr.process_stream(output)
                        if curr.has_output():
                            output = curr.output()
                        else:
                            output = None
                        # more output to come?
                        if curr.has_output():
                            self.pending_filters.append(curr)
                    else:
                        output = curr.process(output)

                # no output produced, ignored rest of filters
                if output is None:
                    break

                # last filter -> return value
                if (i == len(self.filters) - 1) and (output is not None):
                    return output

            # have we finished processing all the data?
            self.finished = len(self.pending_filters) == 0

        raise StopIteration()


def filter_data(data: Any, filters: Optional[Union[BatchFilter, List[BatchFilter]]], session: Optional[Session] = None) -> Optional[Any]:
    """
    Generator for filtering data.

    :param data: the data to filter
    :param filters: the filter or list of filters to apply sequentially, can be None
    :type filters: Filter or list
    :param session: the optional session object for monitoring the stopped flag
    :type session: Session
    :return: the filtered data, one by one
    """
    iterator = FilterPipelineIterator(data, filters, session=session)
    while True:
        try:
            yield next(iterator)
        except StopIteration:
            break


class MultiFilter(StreamFilter, Initializable):
    """
    Combines multiple filters.
    """

    def __init__(self, filters: List[BatchFilter] = None, logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initialize with the specified filters.

        :param filters: the filters to use
        :type filters: list
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.filters = None if (filters is None) else filters[:]
        self._iterator = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "multi-filter"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Combines multiple filters."

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        if (self.filters is not None) and (len(self.filters) > 0):
            return self.filters[0].accepts()
        else:
            return list()

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        if (self.filters is not None) and (len(self.filters) > 0):
            return self.filters[-1].generates()
        else:
            return list()

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        for f in self.filters:
            f.session = self.session
            init_initializable(f, "filter", raise_again=True)

    def _requires_list_input(self) -> bool:
        """
        Returns whether lists are supported as input.

        :return: True if list inputs are natively handled by the filter
        :rtype: bool
        """
        return True

    def _do_process(self, data):
        """
        Processes the data record.

        :param data: the record to process
        :return: the potentially updated record or None if to drop
        """
        # initialize
        result = []

        # filter data
        if isinstance(data, types.GeneratorType):
            for item in data:
                self._stream_output = []
                self.process_stream(item)
                while self.has_output():
                    result.append(self.output())
        else:
            self._stream_output = []
            self.process_stream(data)
            while self.has_output():
                result.append(self.output())

        # prepare output
        if len(result) == 0:
            result = None
        elif len(result) == 1:
            result = result[0]

        # clean up
        self._stream_output = []

        return result

    def _do_process_stream(self, data):
        """
        Filters the data.

        :param data: the data to filter
        """
        self._iterator = FilterPipelineIterator(data, self.filters, session=self.session)

    def has_output(self) -> bool:
        """
        Whether any output is available.

        :return: True if output can be collected
        :rtype: bool
        """
        if self._iterator is None:
            return False
        try:
            self._stream_output.append(next(self._iterator))
        except:
            pass
        return len(self._stream_output) > 0

    def output(self) -> Optional[Any]:
        """
        Returns the next available output.

        :return: the output, None if nothing to return
        """
        if len(self._stream_output) > 0:
            return self._stream_output.pop(0)
        else:
            return None

    def finalize(self):
        """
        Finishes the processing, e.g., for closing files or databases.
        """
        super().finalize()
        for f in self.filters:
            f.finalize()
