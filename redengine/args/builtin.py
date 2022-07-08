
from typing import Any, Callable

from redengine.core.parameters import BaseArgument
from redengine.core.utils import filter_keyword_args

class SimpleArg(BaseArgument):
    """A simple argument.

    Parameters
    ----------
    value : Any
        Value of the argument.

    """
    def __init__(self, value:Any):
        self._value = value

    def get_value(self, task=None) -> Any:
        return self._value

class Arg(BaseArgument):
    """A simple argument got from the session

    Parameters
    ----------
    value : Any
        Value of the argument.

    """
    def __init__(self, key:Any):
        self.key = key

    def get_value(self, task=None) -> Any:
        return task.session.parameters[self.key]

class Session(BaseArgument):
    "An argument that represents the session"

    def get_value(self, task=None) -> Any:
        return task.session

class Task(BaseArgument):
    "An argument that represents a task"

    def __init__(self, name=None):
        self.name = name

    def get_value(self, task=None) -> Any:
        if self.name is None:
            return task
        else:
            return task.session[self.name]

class Return(BaseArgument):
    """A return argument

    Return is an argument which value represents
    the return of a task.

    Parameters
    ----------
    name : str
        Name of the task which return value the argument 
        represents.

    Examples
    --------

    .. code-block:: python

        from redengine.arguments import Return
        from redengine.tasks import FuncTask

        # Create a task with a return
        @FuncTask()
        def my_task_1():
            ...
            return data

        @FuncTask(parameters={"myarg": Return('my_task_1')})
        def my_task_2(myarg):
            ...
    """

    def __init__(self, task_name, default=None):
        self.task_name = task_name
        self.default = default

    def get_value(self, task=None) -> Any:
        session = task.session
        input_task = session[self.task_name]
        try:
            return session.returns[input_task]
        except KeyError:
            if input_task not in session:
                raise KeyError(f"Task {repr(self.task_name)} does not exists. Cannot get return value")
            return self.default

    def stage(self, task=None):
        return SimpleArg(self.get_value(task))

class FuncArg(BaseArgument):
    """An argument which value is defined by the 
    return value of given function.

    Parameters
    ----------
    func : Callable
        Function that is executed and passed as value.
    *args : tuple
        Positional arguments passed to func.
    **kwargs : dict
        Keyword arguments passed to func.

    Examples
    --------

    Simple example:

    .. code-block:: python

        from redengine.tasks import FuncTask
        from redengine.arguments import FuncArg

        def my_func():
            ...
            return obj

        @FuncTask(parameters={"my_param": FuncArg(my_func)})
        def my_task(my_param):
            ...

    Example to set to session:

    .. doctest:: funcarg

        >>> from redengine.arguments import FuncArg

    The ``session.parameters`` were updated.

    .. doctest:: funcarg

        >>> from redengine import session
        >>> session.parameters
        Parameters(myarg1=FuncArg(myarg1), myarg2=FuncArg(myfunc))
    """
    def __init__(self, __func:Callable, *args, **kwargs):
        self.func = __func
        self.args = args
        self.kwargs = self._get_kwargs(kwargs)

    def _get_kwargs(self, kwargs):
        defaults = {
            "session": self.session,
        }
        defaults.update(kwargs)
        return filter_keyword_args(self.func, defaults)

    def get_value(self, task=None):
        return self(task=task)

    def __call__(self, **kwargs):
        kwargs.update(self.kwargs)
        kwargs = filter_keyword_args(self.func, kwargs)
        return self.func(*self.args, **kwargs)

    def __repr__(self):
        cls_name = type(self).__name__
        return f'{cls_name}({self.func.__name__})'