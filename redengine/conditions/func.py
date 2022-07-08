
import copy
from typing import Callable, List, Optional, Pattern, Union


from redengine.session import Session
from redengine.core.condition import BaseCondition

class FuncCond(BaseCondition):
    """Condition from a function.

    This class is to create conditions directly from
    functions.

    Parameters
    ----------
        func : callable
            Function that should return True or False 
            depending on the state of the condition.
            Can also be passed later as decorator.
        syntax : str, Patter, list
            String, regex pattern or list of such to be 
            passed to the string parser.
        args : tuple
            Argumnets to be passed to the function.
            Optional
        kwargs : dict
            Keyword arguments to be passed to the function.
            Optional

    Examples
    --------

    >>> from redengine.conditions import FuncCond
    >>> from redengine.parse import parse_condition

    Simple example:

    >>> @FuncCond(syntax="is foo")
    ... def is_foo():
    ...     ...
    ...     return True

    >>> parse_condition("is foo")
    FuncCond(is_foo, syntax='is foo', args=(), kwargs={})

    You can also have named parameters (using regex groups)
    to be passed to the function:

    >>> import re
    >>> @FuncCond(syntax=re.compile(r"is foo in (?P<myval>.+)"))
    ... def is_foo(myval):
    ...     ...
    ...     if myval == "house":
    ...         return True
    ...     else:
    ...         return False

    >>> parse_condition("is foo in house")
    FuncCond(is_foo, syntax=re.compile('is foo in (?P<myval>.+)'), args=(), kwargs={'myval': 'house'})
    """

    def __init__(self, 
                 func:Callable[..., bool]=None,
                 syntax:Union[str, Pattern, List[Union[str, Pattern]]]=None, 
                 args:Optional[tuple]=None, 
                 kwargs:Optional[dict]=None,
                 session=None):

        self.func = func
        self.syntax = syntax
        self.args = () if args is None else args
        self.kwargs = {} if kwargs is None else kwargs
        if session:
            self.session = session
        if self.syntax is not None:
            self._set_parsing()

    def _recreate(self, *args, **kwargs) -> 'FuncCond':
        "Recreate the condition using args and kwargs"
        new_self = copy.copy(self)
        new_self.args = args
        new_self.kwargs = kwargs
        return new_self

    def __call__(self, func: Callable[..., bool]):
        if self.func is not None:
            raise ValueError("Function for the condition is already set")
        self.func = func
        return func # To prevent problems with pickling

    def __bool__(self):
        return self.func(*self.args, **self.kwargs)

    def _set_parsing(self):

        session = self.session

        syntaxes = [self.syntax] if not isinstance(self.syntax, (list, tuple, set)) else self.syntax
        for syntax in syntaxes:
            session._cond_parsers[syntax] = self._recreate

    def __repr__(self):
        cls_name = type(self).__name__
        func_name = self.func.__name__
        syntax = repr(self.syntax)
        return f'{cls_name}({func_name}, syntax={syntax}, args={repr(self.args)}, kwargs={repr(self.kwargs)})'