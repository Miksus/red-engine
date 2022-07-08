
from typing import Any, TYPE_CHECKING
from abc import abstractmethod

from redengine._base import RedBase

if TYPE_CHECKING:
    import redengine

class BaseArgument(RedBase):
    """Base class for Arguments.
    
    Argument is a wrapper for value that can be 
    passed to a task. The value can be formulated
    on the fly or it can be a constant variable.

    Examples
    --------

    Minimum example:

    >>> from redengine.core import BaseArgument
    >>> class MyArgument(BaseArgument):
    ...     def __init__(self, value):
    ...         self.value = value
    ...
    ...     def get_value(self):
    ...         value = self.value
    ...         ... # Code that forms the argument value
    ...         return value
    ...
    >>> from redengine.core import Parameters
    >>> Parameters(myarg=MyArgument("value"))
    Parameters(myarg=MyArgument('value'))

    """
    session: 'redengine.Session'
    
    @abstractmethod
    def get_value(self, task:'redengine.core.Task'=None) -> Any:
        """Get the actual value of the argument.
        Override for custom behaviour.

        Parameters
        ----------
        task : redengine.core.Task, optional
            Task that requested the value of the argument.
        """

    def stage(self, task:'redengine.core.Task'=None) -> 'BaseArgument':
        """Get (a copy of) the argument with a 
        value that can be passed to child threads
        or processes. Override for custom behaviour.

        Example use cases:

            - Save a complex object to disk and read 
              it again later with ``get_value``.
            - Shut a file buffer and reopen it when
              in the child process/thread.
            - Remove non-picklable attributes.

        Parameters
        ----------
        task : redengine.core.Task, optional
            Task that requested the value of the argument.

        Notes
        -----
        It is advisable to copy the argument in order
        not to interfere with the passing of the argument
        in later situations.

        Returns
        -------
        BaseArgument
            Argument that is ready to be passed to a child
            thread or process.
        """
        return self

    def __eq__(self, other):
        if isinstance(other, BaseArgument):
            return self.get_value() == other.get_value()
        else:
            return self.get_value() == other

    def __repr__(self):
        cls_name = type(self).__name__
        return f'{cls_name}({repr(self.get_value())})'

    def __str__(self):
        return str(self.get_value())
