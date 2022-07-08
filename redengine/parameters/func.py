
from typing import Callable
from redengine.args import FuncArg

class FuncParam:
    """A parameter from a function.

    This class is to create parameters directly from
    functions.

    Parameters
    ----------
        name : str
            Name of the parameter, by default
            the name of the function.

    Examples
    --------

    Simple example:

    >>> from redengine.parameters import FuncParam
    >>> @FuncParam()
    ... def email_list():
    ...     ...
    ...     return ['me@example.com']

    Create a task that uses the parameter:

    >>> from redengine.tasks import FuncTask
    >>> @FuncTask()
    >>> def send_things(email_list):
        ... # Send email list

    """
    def __init__(self, name=None, session=None):
        self.name = name
        self.session = session

    def __call__(self, func: Callable):
        session = FuncArg.session if self.session is None else self.session
        name = self._get_name(func)
        session.parameters[name] = FuncArg(func)
        return func

    def _get_name(self, func):
        if self.name is not None:
            return self.name
        else:
            return func.__name__