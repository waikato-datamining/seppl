import traceback
from typing import Union, List, Optional

from seppl import init_initializable, Initializable, Session
from ._reader import Reader
from ._filter import Filter, MultiFilter
from ._writer import Writer, StreamWriter, BatchWriter


def execute(reader: Reader, filters: Optional[Union[Filter, List[Filter]]], writer: Writer,
            session: Session = None):
    """
    Executes the pipeline.

    :param reader: the reader to use
    :type reader: Reader
    :param filters: the filter(s) to use, can be None
    :type filters: list or Filter
    :param writer: the writer to use
    :type writer: Writer
    :param session: the session object to use, creates default one if None
    :type session: Session
    """
    # assemble filter
    if isinstance(filters, Filter):
        filter_ = filters
    elif isinstance(filters, list):
        filter_ = MultiFilter(filters=filters)
    elif filters is None:
        filter_ = None
    else:
        raise Exception("Unhandled filter(s) type: %s" % str(type(filters)))

    # propagate session
    if session is None:
        session = Session()
    reader.session = session
    if filter_ is not None:
        filter_.session = session
    if writer is not None:
        writer.session = session

    # initialize
    if isinstance(reader, Initializable) and not init_initializable(reader, "reader"):
        return
    if (filter_ is not None) and isinstance(filter_, Initializable) and not init_initializable(filter_, "filter"):
        return
    if (writer is not None) and isinstance(writer, Initializable) and not init_initializable(writer, "writer"):
        return

    # process data
    try:
        while not reader.has_finished():
            if isinstance(writer, BatchWriter):
                data = []
                if session.options.force_batch:
                    for item in reader.read():
                        if item is None:
                            continue
                        session.count += 1
                        data.append(item)
                        if session.count % session.options.update_interval == 0:
                            session.logger.info("%d records read..." % session.count)
                    if filter_ is not None:
                        data = filter_.process(data)
                        session.logger.info("%d records filtered..." % session.count)
                else:
                    for item in reader.read():
                        if item is None:
                            continue
                        session.count += 1
                        if (filter_ is not None) and (item is not None):
                            item = filter_.process(item)
                        if item is not None:
                            if not isinstance(item, list):
                                item = [item]
                            data.extend(item)
                        if session.count % session.options.update_interval == 0:
                            session.logger.info("%d records processed..." % session.count)
                writer.write_batch(data)
            elif isinstance(writer, StreamWriter) or (writer is None):
                if session.options.force_batch:
                    data = []
                    for item in reader.read():
                        if item is None:
                            continue
                        session.count += 1
                        data.append(item)
                        if session.count % session.options.update_interval == 0:
                            session.logger.info("%d records read..." % session.count)
                    if filter_ is not None:
                        count = len(data)
                        data = filter_.process(data)
                        session.logger.info("%d records filtered..." % count)
                    if not isinstance(data, list):
                        data = [data]
                    if writer is not None:
                        count = 0
                        for item in data:
                            count += 1
                            writer.write_stream(item)
                            if count % session.options.update_interval == 0:
                                session.logger.info("%d records written..." % count)
                else:
                    for item in reader.read():
                        if item is None:
                            continue
                        session.count += 1
                        if (filter_ is not None) and (item is not None):
                            item = filter_.process(item)
                        if item is not None:
                            if writer is not None:
                                writer.write_stream(item)
                        if session.count % session.options.update_interval == 0:
                            session.logger.info("%d records processed..." % session.count)
            else:
                raise Exception("Neither BatchWriter nor StreamWriter!")
        session.logger.info("%d records processed in total." % session.count)
    except:
        traceback.print_exc()

    # clean up
    if isinstance(reader, Initializable):
        reader.finalize()
    if (filter_ is not None) and isinstance(filter_, Initializable):
        filter_.finalize()
    if (writer is not None) and isinstance(writer, Initializable):
        writer.finalize()
