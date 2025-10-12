import traceback
from typing import Union, List, Optional

from seppl import init_initializable, Initializable, Session
from ._filter import BatchFilter, filter_data
from ._reader import Reader, InfiniteReader
from ._writer import Writer, StreamWriter, BatchWriter


def _stream_execution(reader: Reader, filters_: Optional[Union[BatchFilter, List[BatchFilter]]], writer: Optional[Writer], session: Session):
    """
    Executes the pipeline in streaming mode.

    :param reader: the reader to use
    :type reader: Reader
    :param filters_: the filter or list of filters to use, can be None
    :type filters_: list or Filter
    :param writer: the writer to use
    :type writer: Writer
    :param session: the session object to use
    :type session: Session
    """
    while True:
        for item in reader.read():
            if item is None:
                continue
            if session.stopped:
                return
            session.count += 1
            for filtered in filter_data(item, filters_, session=session):
                if session.stopped:
                    return
                if filtered is not None:
                    if writer is not None:
                        if isinstance(writer, StreamWriter):
                            writer.write_stream(filtered)
                        elif isinstance(writer, BatchWriter):
                            writer.write_batch(filtered)
                if session.count % session.options.update_interval == 0:
                    session.logger.info("%d records processed..." % session.count)
        if reader.has_finished():
            break


def _batch_execution(reader: Reader, filters_: Optional[Union[BatchFilter, List[BatchFilter]]], writer: Optional[Writer], session: Session):
    """
    Executes the pipeline in batch mode.

    :param reader: the reader to use
    :type reader: Reader
    :param filters_: the filter or list of filters to use, can be None
    :type filters_: list or Filter
    :param writer: the writer to use
    :type writer: Writer
    :param session: the session object to use
    :type session: Session
    """
    data = []
    while True:
        for item in reader.read():
            if item is None:
                continue
            if session.stopped:
                return
            session.count += 1
            data.append(item)
            if session.count % session.options.update_interval == 0:
                session.logger.info("%d records read..." % session.count)
        if reader.has_finished():
            break

    if session.stopped:
        return

    if filters_ is not None:
        filtered_data = []
        for filtered in filter_data(data, filters_, session=session):
            if session.stopped:
                return
            if isinstance(filtered, list):
                filtered_data.extend(filtered)
            else:
                filtered_data.append(filtered)
        session.logger.info("%d records filtered..." % session.count)
        data = filtered_data

    if session.stopped:
        return

    if writer is not None:
        if isinstance(writer, StreamWriter):
            count = 0
            for item in data:
                count += 1
                writer.write_stream(item)
                if count % session.options.update_interval == 0:
                    session.logger.info("%d records written..." % count)
        elif isinstance(writer, BatchWriter):
            writer.write_batch(data)
        else:
            raise Exception("Neither stream nor batch writer: %s" % str(type(writer)))


def execute(reader: Reader, filters: Optional[Union[BatchFilter, List[BatchFilter]]], writer: Optional[Writer],
            session: Session = None, pre_initialize=None, post_finalize=None):
    """
    Executes the pipeline.

    :param reader: the reader to use
    :type reader: Reader
    :param filters: the filter(s) to use, can be None
    :type filters: list or Filter
    :param writer: the writer to use, can be None
    :type writer: Writer
    :param session: the session object to use, creates default one if None
    :type session: Session
    :param pre_initialize: optional method to execute before the plugins get initialized, takes the session object as only parameter
    :param post_finalize: optional method to execute after the plugins have been finalized, takes the session object as only parameter
    """
    # assemble filter
    if isinstance(filters, BatchFilter):
        filters_ = [filters]
    elif isinstance(filters, list):
        filters_ = filters
    elif filters is None:
        filters_ = []
    else:
        raise Exception("Unhandled filter(s) type: %s" % str(type(filters)))

    # propagate session
    if session is None:
        session = Session()
    reader.session = session
    if filters_ is not None:
        for filter_ in filters_:
            filter_.session = session
    if writer is not None:
        writer.session = session

    # custom initialization?
    if pre_initialize is not None:
        pre_initialize(session)

    # initialize
    if isinstance(reader, Initializable) and not init_initializable(reader, "reader"):
        return
    for filter_ in filters_:
        if isinstance(filter_, Initializable) and not init_initializable(filter_, "filter"):
            return
    if (writer is not None) and isinstance(writer, Initializable) and not init_initializable(writer, "writer"):
        return

    # batch mode?
    batch_mode = session.options.force_batch or isinstance(writer, BatchWriter)
    if isinstance(reader, InfiniteReader) and reader.is_infinite():
        if session.options.force_batch:
            session.logger.warning("Reader produces data infinitely, disabling batch mode!")
        batch_mode = False

    # process data
    try:
        if batch_mode:
            _batch_execution(reader, filters_, writer, session)
        else:
            _stream_execution(reader, filters_, writer, session)
        session.logger.info("%d records processed in total." % session.count)
    except:
        traceback.print_exc()

    # clean up
    if isinstance(reader, Initializable):
        reader.finalize()
    for filter_ in filters_:
        if isinstance(filter_, Initializable):
            filter_.finalize()
    if (writer is not None) and isinstance(writer, Initializable):
        writer.finalize()

    # custom finalization?
    if post_finalize is not None:
        post_finalize(session)
