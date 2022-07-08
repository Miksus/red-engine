import datetime
from abc import abstractmethod
from typing import Callable, Dict, Pattern, Union, Type

from redengine._base import RedBase
from redengine.core.meta import _add_parser, _register
from redengine.session import Session


CLS_CONDITIONS: Dict[str, Type['BaseCondition']] = {}
PARSERS: Dict[Union[str, Pattern], Union[Callable, 'BaseCondition']] = {}


class _ConditionMeta(type):
    def __new__(mcs, name, bases, class_dict):

        cls = type.__new__(mcs, name, bases, class_dict)

        # Store the name and class for configurations
        # so they can be used in dict construction
        _register(cls, CLS_CONDITIONS)

        # Add the parsers
        if cls.session is None:
            # Red engine default conditions
            # storing to the class
            _add_parser(cls, container=Session._cls_cond_parsers)
        else:
            # User defined conditions
            # storing to the object
            _add_parser(cls, container=Session._cls_cond_parsers)
        return cls


class BaseCondition(RedBase, metaclass=_ConditionMeta):
    """A condition is a thing/occurence that should happen in 
    order to something happen.

    Conditions are used to determine whether a task can be started,
    a task should be terminated or the scheduler should shut 
    down. Conditions are either true or false.

    A condition could answer for any of the following questions:
        - Current time is as specified (ie. Monday afternoon).
        - A given task has already run.
        - The machine has at least a given amount of RAM.
        - A specific file exists.

    Each condition should have the method ``__bool__`` specified
    as minimum. This method should return ``True`` or ``False``
    depending on whether the condition holds or does not hold.  

    Examples
    --------

    Minimum example:

    >>> from redengine.core import BaseCondition
    >>> class MyCondition(BaseCondition):
    ...     def __bool__(self):
    ...         ... # Code that defines state either 
    ...         return True

    Complicated example with parser:

    >>> import os, re
    >>> class IsFooBar(BaseCondition):
    ...     __parsers__ = {
    ...         re.compile(r"is foo '(?P<outcome>.+)'"): "__init__"
    ...     }
    ...
    ...     def __init__(self, outcome):
    ...         self.outcome = outcome
    ...
    ...     def __bool__(self):
    ...         return self.outcome == "bar"
    ...
    ...     def __repr__(self):
    ...         return f"IsFooBar('{self.outcome}')"
    ...
    >>> from redengine.parse import parse_condition
    >>> parse_condition("is foo 'bar'")
    IsFooBar('bar')

    """
    # The session (set in redengine.session)
    session: Session

    __parsers__ = {}
    __register__ = False

    @abstractmethod
    def __bool__(self) -> bool:
        """Check whether the condition holds.
        Override this method."""

    def __and__(self, other):
        # self & other
        # bitwise and
        # using & operator

        return All(self, other)

    def __or__(self, other):
        # self | other
        # bitwise or

        return Any(self, other)

    def __invert__(self):
        # ~self
        # bitwise not
        return Not(self)

    def __eq__(self, other):
        "Equal operation"
        is_same_class = isinstance(other, type(self))
        return is_same_class

    def __str__(self):
        if hasattr(self, "_str"):
            return self._str
        else:
            raise AttributeError(f"Condition {type(self)} is missing __str__.")


class _ConditionContainer:
    "Wraps another condition"

    def __getitem__(self, val):
        return self.subconditions[val]

    def __iter__(self):
        return iter(self.subconditions)

    def __eq__(self, other):
        "Equal operation"
        is_same_class = isinstance(other, type(self))
        if is_same_class:
            return self.subconditions == other.subconditions
        else:
            return False

    def __repr__(self):
        string = ', '.join(map(str, self.subconditions))
        return f'{type(self).__name__}({string})'

class Any(_ConditionContainer, BaseCondition):

    def __init__(self, *conditions):
        self.subconditions = []

        self_type = type(self)
        for cond in conditions:
            # Avoiding nesting (like Any(Any(...), ...) --> Any(...))
            conds = cond.subconditions if isinstance(cond, self_type) else [cond]
            self.subconditions += conds

    def __bool__(self):
        return any(self.subconditions)

    def __str__(self):
        try:
            return super().__str__()
        except AttributeError:
            string = ' | '.join(map(str, self.subconditions))
            return f'({string})'


class All(_ConditionContainer, BaseCondition):

    def __init__(self, *conditions):
        self.subconditions = []

        self_type = type(self)
        for cond in conditions:
            # Avoiding nesting (like All(All(...), ...) --> All(...))
            conds = cond.subconditions if isinstance(cond, self_type) else [cond]
            self.subconditions += conds

    def __bool__(self):
        return all(self.subconditions)

    def __str__(self):
        try:
            return super().__str__()
        except AttributeError:
            string = ' & '.join(map(str, self.subconditions))
            return f'({string})'

    def __getitem__(self, val):
        return self.subconditions[val]


class Not(_ConditionContainer, BaseCondition):

    def __init__(self, condition):
        # TODO: rename condition as child
        self.condition = condition

    def __bool__(self):
        return not(self.condition)

    def __repr__(self):
        string = repr(self.condition)
        return f'~{string}'

    def __str__(self):
        try:
            return super().__str__()
        except AttributeError:
            string = str(self.condition)
            return f'~{string}'

    @property
    def subconditions(self):
        return (self.condition,)

    def __iter__(self):
        return iter((self.condition,))
        
    def __invert__(self):
        "inverse of inverse is the actual condition"
        return self.condition

    def __eq__(self, other):
        "Equal operation"
        is_same_class = isinstance(other, type(self))
        if is_same_class:
            return self.condition == other.condition
        else:
            return False


class AlwaysTrue(BaseCondition):
    "Condition that is always true"
    def __bool__(self):
        return True

    def __repr__(self):
        return 'AlwaysTrue'

    def __str__(self):
        try:
            return super().__str__()
        except AttributeError:
            return 'true'


class AlwaysFalse(BaseCondition):
    "Condition that is always false"

    def __bool__(self):
        return False

    def __repr__(self):
        return 'AlwaysFalse'

    def __str__(self):
        try:
            return super().__str__()
        except AttributeError:
            return 'false'
