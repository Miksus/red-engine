from logging.handlers import QueueHandler as _QueueHandler
from logging import Formatter

import copy

# Copying the default formatter mechanism from logging
_DEFAULT_FORMATTER = Formatter()

class QueueHandler(_QueueHandler):
    """
    The logging.handlers.QueueHandler gives priority for the message but does
    not maintain the other info in a record when passing it to the queue. 
    These 
    """

    def prepare(self, record):
        """
        Prepare a record for queuing. The object returned by this method is
        enqueued.

        The base implementation formats the record to merge the message and
        arguments, and removes unpickleable items from the record in-place.
        Specifically, it overwrites the record's `msg` and
        `message` attributes with the merged message (obtained by
        calling the handler's `format` method), and sets the `args`,
        `exc_info` and `exc_text` attributes to None.

        You might want to override this method if you want to convert
        the record to a dict or JSON string, or send a modified copy
        of the record while leaving the original intact.
        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also returns the formatted
        # message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info and exc_text attributes, as they are no longer
        # needed and, if not None, will typically not be pickleable.
        msg = self.format(record)
        # bpo-35726: make copy of record to avoid affecting other handlers in the chain.
        record = copy.copy(record)
        record.message = msg
        # record.msg = msg
        record.args = None
        record.exc_info = None
        # record.exc_text = None
        return record
