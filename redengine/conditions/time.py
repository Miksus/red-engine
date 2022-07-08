
import datetime

from redengine.time import TimeOfDay, TimeOfWeek, TimeDelta
from redengine.time.construct import get_full_cycle, get_between, get_after, get_before
from redengine.core.condition.base import BaseCondition

class IsPeriod(BaseCondition):
    """Condition for checking whether current time
    is in the given time period. 

    Parameters
    ----------
    period : redengine.core.time.TimePeriod
        Time period to check.

    Examples
    --------

    **Parsing example:**

    >>> from redengine.parse import parse_condition
    >>> parse_condition("time of day between 10:00 and 15:00")
    IsPeriod(period=TimeOfDay('10:00', '15:00'))

    **Construction example:**

    >>> from redengine.conditions import IsPeriod
    >>> from redengine.time import TimeOfDay
    >>> is_morning = IsPeriod(period=TimeOfDay("06:00", "12:00")) # doctest: +SKIP
    """
    def __init__(self, period):
        if isinstance(period, TimeDelta):
            raise AttributeError("TimeDelta does not have __contains__.")
        self.period = period

    def __bool__(self):
        return datetime.datetime.now() in self.period

    def __str__(self):
        if hasattr(self, "_str"):
            return self._str
        elif hasattr(self, "period"):
            return f'is {str(self.period)}'
        else:
            return type(self).__name__

    def __repr__(self):
        cls_name = type(self).__name__
        return f"{cls_name}(period={repr(self.period)})"

    @classmethod
    def _from_parser(cls, span_type, **kwargs):
        period_func = {
            "between": get_between,
            "after": get_after,
            "before": get_before,
        }[span_type]
        period = period_func(**kwargs)
        return cls(period=period)

