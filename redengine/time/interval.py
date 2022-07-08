
import calendar
import re

import dateutil
import pandas as pd

from redengine.core.time.anchor import AnchoredInterval
from redengine.core.time.base import TimeInterval
from redengine.core.time.utils import timedelta_to_str, to_dict, to_nanoseconds


class TimeOfMinute(AnchoredInterval):
    """Time interval anchored to minute cycle of a clock

    min: 0 seconds, 0 microsecond, 0 nanosecond
    max: 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From 5th second of a minute to 30th second of a minute
        TimeOfHour("5:00", "30:00")
    """

    _scope = "minute"
    _scope_max = to_nanoseconds(minute=1) - 1 # See: pd.Timedelta(59999999999, unit="ns")
    _unit_resolution = to_nanoseconds(second=1)

    def anchor_str(self, s, **kwargs):
        # ie. 30.123
        res = re.search(r"(?P<second>[0-9][0-9])([.](?P<microsecond>[0-9]{0,6}))?(?P<nanosecond>[0-9]+)?", s, flags=re.IGNORECASE)
        if res:
            if res["microsecond"] is not None:
                res["microsecond"] = res["microsecond"].ljust(6, "0")
            return to_nanoseconds(**{key: int(val) for key, val in res.groupdict().items() if val is not None})

        res = re.search(r"(?P<n>[1-4] ?(quarter|q))", s, flags=re.IGNORECASE)
        if res:
            # ie. "1 quarter"
            n_quarters = res["n"]
            return (self._scope_max + 1) / 4 * n_quarters - 1


class TimeOfHour(AnchoredInterval):
    """Time interval anchored to hour cycle of a clock

    min: 0 minutes, 0 seconds, 0 microsecond, 0 nanosecond
    max: 59 minutes, 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From 15 past to half past
        TimeOfHour("15:00", "30:00")
    """
    _scope = "hour"
    _scope_max = to_nanoseconds(hour=1) - 1
    _unit_resolution = to_nanoseconds(minute=1)

    def anchor_str(self, s, **kwargs):
        # ie. 12:30.123
        res = re.search(r"(?P<minute>[0-9][0-9]):(?P<second>[0-9][0-9])([.](?P<microsecond>[0-9]{0,6}))?(?P<nanosecond>[0-9]+)?", s, flags=re.IGNORECASE)
        if res:
            if res["microsecond"] is not None:
                res["microsecond"] = res["microsecond"].ljust(6, "0")
            return to_nanoseconds(**{key: int(val) for key, val in res.groupdict().items() if val is not None})

        res = re.search(r"(?P<n>[1-4]) ?(quarter|q)", s, flags=re.IGNORECASE)
        if res:
            # ie. "1 quarter"
            n_quarters = int(res["n"])
            return (self._scope_max + 1) / 4 * n_quarters - 1


class TimeOfDay(AnchoredInterval):
    """Time interval anchored to day cycle of a clock
    
    min: 0 hours, 0 minutes, 0 seconds, 0 microsecond, 0 nanosecond
    max: 23 hours, 59 minutes, 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From 10 o'clock to 15 o'clock
        TimeOfDay("10:00", "15:00")
    """
    _scope = "day"
    _scope_max = to_nanoseconds(day=1) - 1
    _unit_resolution = to_nanoseconds(hour=1)

    def anchor_str(self, s, **kwargs):
        # ie. "10:00:15"
        dt = dateutil.parser.parse(s)
        d = to_dict(dt)
        components = ("hour", "minute", "second", "microsecond", "nanosecond")
        return to_nanoseconds(**{key: int(val) for key, val in d.items() if key in components})

    def anchor_dt(self, dt, **kwargs):
        "Turn datetime to nanoseconds according to the scope (by removing higher time elements)"
        d = to_dict(dt)
        d = {
            key: val
            for key, val in d.items()
            if key in ("hour", "minute", "second", "microsecond", "nanosecond")
        }
        return to_nanoseconds(**d) 

class TimeOfWeek(AnchoredInterval):
    """Time interval anchored to week cycle
    
    min: Monday, 0 hours, 0 minutes, 0 seconds, 0 microsecond, 0 nanosecond
    max: Sunday, 23 hours, 59 minutes, 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From Monday 3 PM to Wednesday 4 PM
        TimeOfWeek("Mon 15:00", "Wed 16:00")
    """
    _scope = "week"
    _scope_max = to_nanoseconds(day=7) - 1 # Sun day end of day 
    _unit_resolution = to_nanoseconds(day=1)

    weeknum_mapping = {
        **dict(zip(calendar.day_name, range(7))), 
        **dict(zip(calendar.day_abbr, range(7))), 
        **dict(zip(range(7), range(7)))
    }
    # TODO: ceil end
    def anchor_str(self, s, side=None, **kwargs):
        # Allowed:
        #   "Mon", "Monday", "Mon 10:00:00"
        res = re.search(r"(?P<dayofweek>[a-z]+) ?(?P<time>.*)", s, flags=re.IGNORECASE)
        comps = res.groupdict()
        dayofweek = comps.pop("dayofweek")
        time = comps.pop("time")
        nth_day = self.weeknum_mapping[dayofweek]

        # TODO: TimeOfDay.anchor_str as function
        if not time:
            nanoseconds = to_nanoseconds(day=1) - 1 if side == "end" else 0
        else:
            nanoseconds = TimeOfDay().anchor_str(time) 

        return to_nanoseconds(day=1) * nth_day + nanoseconds

    def anchor_dt(self, dt, **kwargs):
        "Turn datetime to nanoseconds according to the scope (by removing higher time elements)"
        d = to_dict(dt)
        d = {
            key: val
            for key, val in d.items()
            if key in ("hour", "minute", "second", "microsecond", "nanosecond")
        }
        dayofweek = dt.weekday()
        return to_nanoseconds(**d) + dayofweek * to_nanoseconds(day=1)


class TimeOfMonth(AnchoredInterval):
    """Time interval anchored to day cycle of a clock
    
    min: first day of month, 0 hours, 0 minutes, 0 seconds, 0 microsecond, 0 nanosecond
    max: last day of month, 23 hours, 59 minutes, 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From 10 o'clock to 15 o'clock
        TimeOfMonth("1st", "5th")
    """
    # TODO: Support for month end (ie. last 5th day of month to last 2nd)
    # Could be implemented by allowing minus _start and minus _end
    #   rollforward/rollback/contains would need slight changes 

    _scope = "year"
    _scope_max = to_nanoseconds(day=31) - 1 # 31st end of day
    _unit_resolution = to_nanoseconds(day=1)
     # NOTE: Floating
    # TODO: ceil end and implement reversion (last 5th day)

    def anchor_str(self, s, side=None, **kwargs):
        # Allowed:
        #   "5th", "1st", "5", "3rd 12:30:00"
        #   TODO: "first 5th", "last 5th", "last 3rd 10:00:00"
        res = re.search(r"(?P<dayofmonth>[0-9]+)(st|nd|rd|th|[.])? ?(?P<time>.*)", s, flags=re.IGNORECASE)
        comps = res.groupdict()
        dayofmonth = comps.pop("dayofmonth")
        time = comps.pop("time")
        nth_day = int(dayofmonth)

        # TODO: TimeOfDay.anchor_str as function
        ceil_time = not time and side == "end"
        if ceil_time:
            # If time is not defined and the end
            # is being anchored, the time is ceiled.

            # If one says 'thing X was organized between 
            # 15th and 17th of July', the sentence
            # includes 17th till midnight.
            nanoseconds = to_nanoseconds(day=1) - 1
        elif time:
            nanoseconds = TimeOfDay().anchor_str(time) 
        else:
            nanoseconds = 0

        return to_nanoseconds(day=1) * (nth_day - 1) + nanoseconds

    def anchor_int(self, i, **kwargs):
        return i * self._unit_resolution

    def anchor_dt(self, dt, **kwargs):
        "Turn datetime to nanoseconds according to the scope (by removing higher time elements)"
        d = to_dict(dt)
        d = {
            key: val
            for key, val in d.items()
            if key in ("day", "hour", "minute", "second", "microsecond", "nanosecond")
        }
        if "day" in d:
            # Day (of month) does not start from 0 (but from 1)
            d["day"] = d["day"] - 1

        return to_nanoseconds(**d)

    def get_scope_forward(self, dt):
        n_days = calendar.monthrange(dt.year, dt.month)[1]
        return to_nanoseconds(day=1) * n_days

    def get_scope_back(self, dt):
        month = 12 if dt.month == 1 else dt.month - 1
        year = dt.year - 1 if dt.month == 1 else dt.year
        n_days = calendar.monthrange(year, month)[1]
        return to_nanoseconds(day=1) * n_days

class TimeOfYear(AnchoredInterval):
    """Time interval anchored to day cycle of a clock

    min: 1st Jan, 0 hours, 0 minutes, 0 seconds, 0 microsecond, 0 nanosecond
    max: 31st Dec, 23 hours, 59 minutes, 59 seconds, 999999 microsecond, 999 nanosecond

    Example:
        # From 10 o'clock to 15 o'clock
        TimeOfYear("Jan", "Feb")
    """

    _scope = "year"
    _scope_max = to_nanoseconds(day=1) * 366 - 1

    monthnum_mapping = {
        **dict(zip(calendar.month_name[1:], range(12))), 
        **dict(zip(calendar.month_abbr[1:], range(12))), 
        **dict(zip(range(12), range(12)))
    }
    # NOTE: Floating

    def anchor_str(self, s, side=None, **kwargs):
        # Allowed:
        #   "January", "Dec", "12", "Dec last 5th 10:00:00"
        res = re.search(r"(?P<monthofyear>[a-z]+) ?(?P<month>.*)", s, flags=re.IGNORECASE)
        comps = res.groupdict()
        monthofyear = comps.pop("monthofyear")
        month_str = comps.pop("month")
        nth_month = self.monthnum_mapping[monthofyear]

        # TODO: TimeOfDay.anchor_str as function
        # nanoseconds = TimeOfMonth().anchor_str(month_str) if month_str else 0

        ceil_time = not month_str and side == "end"
        if ceil_time:
            # If time is not defined and the end
            # is being anchored, the time is ceiled.

            # If one says 'thing X was organized between 
            # 15th and 17th of July', the sentence
            # includes 17th till midnight.
            nanoseconds = to_nanoseconds(day=31) - 1 
        elif month_str:
            nanoseconds = TimeOfMonth().anchor_str(month_str) 
        else:
            nanoseconds = 0

        return nth_month * to_nanoseconds(day=31) + nanoseconds

    def anchor_dt(self, dt, **kwargs):
        "Turn datetime to nanoseconds according to the scope (by removing higher time elements)"
        dt_dict = to_dict(dt)
        d = {
            key: val
            for key, val in dt_dict.items()
            if key in ("day", "hour", "minute", "second", "microsecond", "nanosecond")
        }
        nth_month = dt_dict["month"] - 1
        if "day" in d:
            # Day (of month) does not start from 0 (but from 1)
            d["day"] = d["day"] - 1
        return nth_month * to_nanoseconds(day=31) + to_nanoseconds(**d)


class RelativeDay(TimeInterval):
    """Specific day

    Examples:
    ---------
        Day("today")
        Day("yesterday")
        Day("yesterday")
    """

    offsets = {
        "today": pd.Timedelta("0 day"),
        "yesterday": pd.Timedelta("1 day"),
        "the_day_before": pd.Timedelta("2 day"),
        #"first_day_of_year": get_first_day_of_year,
    }

    def __init__(self, day, *, start_time=None, end_time=None):
        self.day = day
        self.start_time = self.min.date() if start_time is None else start_time
        self.end_time = self.max.date() if end_time is None else end_time

    def rollback(self, dt):
        offset = self.offsets[self.day]
        dt = dt - offset
        return pd.Interval(
            pd.Timestamp.combine(dt, self.start_time),
            pd.Timestamp.combine(dt, self.end_time)
        )

    def rollforward(self, dt):
        raise AttributeError("RelativeDay has no next day")

    def __repr__(self):
        args_str = str(self.day)
        if self.start_time != self.min.date():
            args_str += f', start_time={self.start_time}'
        if self.end_time != self.max.date():
            args_str += f', end_time={self.end_time}'

        return f"RelativeDay({args_str})"
