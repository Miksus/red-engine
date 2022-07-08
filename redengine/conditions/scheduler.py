
import re

from redengine.core.condition import Comparable, Historical


class SchedulerCycles(Comparable):
    """Condition for whether the scheduler have had
    more/less/equal given amount of cycles of executing
    tasks.

    Examples
    --------

    **Parsing example:**

    >>> from redengine.parse import parse_condition
    >>> parse_condition("scheduler had more than 3 cycles")
    SchedulerCycles(_gt_=3)
    """

    __parsers__ = {
        re.compile(r"scheduler has more than (?P<_gt_>[0-9]+) cycles"): "__init__",
        re.compile(r"scheduler has less than (?P<_lt_>[0-9]+) cycles"): "__init__",
        re.compile(r"scheduler has (?P<_eq_>[0-9]+) cycles"): "__init__",
    }

    def observe(self, **kwargs):
        return self.session.scheduler.n_cycles

    def __str__(self):
        if hasattr(self, "_str"):
            return self._str
        comps = {"_eq_": "has", "_gt_": "more than", "_lt_": "less than"}
        s = "scheduler"
        for key, val in self.kwargs.items():
            s = s + " has " + comps.get(key, key) + " " + str(val) + " cycles"
        return s

class SchedulerStarted(Historical):
    """Condition for whether the scheduler had started
    in given period.

    Examples
    --------

    **Parsing example:**

    >>> from redengine.parse import parse_condition
    >>> parse_condition("scheduler started 10 minutes ago")
    SchedulerStarted(period=TimeDelta('10 minutes'))

    >>> parse_condition("scheduler has run over 10 minutes")
    ~SchedulerStarted(period=TimeDelta('10 minutes'))
    """

    def observe(self, _start_=None, _end_=None, **kwargs):
        dt = self.session.scheduler.startup_time
        return _start_ <= dt <= _end_

    def __str__(self):
        if hasattr(self, "_str"):
            return self._str
        return f"scheduler {self.period} "