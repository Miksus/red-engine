import datetime
import time
from abc import abstractmethod
from typing import Callable, Dict, List, Pattern, Union
import itertools

import pandas as pd

from redengine._base import RedBase
from redengine.core.meta import _add_parser
from redengine.session import Session

PARSERS: Dict[Union[str, Pattern], Union[Callable, 'TimePeriod']] = {}

class _TimeMeta(type):
    def __new__(mcs, name, bases, class_dict):
        cls = type.__new__(mcs, name, bases, class_dict)
        # Add the parsers
        if cls.session is None:
            # Package defaults
            _add_parser(cls, container=Session._time_parsers)
        else:
            # User defined
            _add_parser(cls, container=cls.session.time_parsers)
        return cls


class TimePeriod(RedBase, metaclass=_TimeMeta):
    """Base for all classes that represent a time period.

    Time period is a period in time with a start and an end.
    These are useful to determine whether an event took 
    place in a specific time span or whether current time 
    is in a given time span.
    """

    resolution = pd.Timestamp.resolution
    min = pd.Timestamp.min
    max = pd.Timestamp.max

    def __contains__(self, other):
        """Whether a given point of time is in
        the TimePeriod"""
        interval = self.rollforward(other)
        return other in interval

    def __and__(self, other):
        # self & other
        # bitwise and
        # using & operator

        return All(self, other)

    def __or__(self, other):
        # self | other
        # bitwise or

        return Any(self, other)

    @abstractmethod
    def rollforward(self, dt):
        "Get previous time interval of the period."
        raise NotImplementedError

    @abstractmethod
    def rollback(self, dt):
        "Get previous time interval of the period."
        raise NotImplementedError

    def next(self, dt):
        "Get next interval (excluding currently ongoing if any)."
        interv = self.rollforward(dt)
        if dt in interv:
            # Offsetting the end point with minimum amount to get new full interval
            interv = self.rollforward(dt.right + self.resolution)
        return interv

    def prev(self, dt):
        "Get previous interval (excluding currently ongoing if any)."
        interv = self.rollback(dt)
        if dt in interv:
            # Offsetting the end point with minimum amount to get new full interval
            interv = self.rollback(dt.left - self.resolution)
        return interv


class TimeInterval(TimePeriod):
    """Base for all time intervals

    Time interval is a period between two fixed but repeating 
    times. Fixed repeated times are defined as time elements
    that repeats constantly but are fixed in a sense that
    if the datetime of an event is known, the question
    whether the event belongs to the period can be answered
    unambigiously.

    Answers to "between 11:00 and 12:00" and "from monday to tuesday"
    """
    _type_name = "interval"
    @abstractmethod
    def __contains__(self, dt):
        "Check whether the datetime is on the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def rollstart(self, dt):
        "Roll forward to next point in time that on the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def rollend(self, dt):
        "Roll back to previous point in time that is on the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def next_start(self, dt):
        "Get next start point of the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def next_end(self, dt):
        "Get next end point of the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def prev_start(self, dt):
        "Get previous start point of the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def prev_end(self, dt):
        "Get pervious end point of the period"
        raise NotImplementedError("Contains not implemented.")

    @abstractmethod
    def from_between(start, end) -> pd.Interval:
        raise NotImplementedError("__between__ not implemented.")

    def rollforward(self, dt):
        "Get next time interval of the period"

        start = self.rollstart(dt)
        end = self.next_end(dt)

        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        
        return pd.Interval(start, end, closed="both")
    
    def rollback(self, dt) -> pd.Interval:
        "Get previous time interval of the period"

        end = self.rollend(dt)
        start = self.prev_start(dt)

        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        
        return pd.Interval(start, end, closed="both")

    def __eq__(self, other):
        "Test whether self and other are essentially the same periods"
        is_same_class = type(self) == type(other)
        if is_same_class:
            return (self._start == other._start) and (self._end == other._end)
        else:
            return False


class TimeDelta(TimePeriod):
    """Base for all time deltas

    Time delta is a period of time from a reference
    point. It is floating in nature as it could
    contain arbitrary datetimes depending on where
    the reference point is set. This reference
    point is typically current datetime.
    """
    _type_name = "delta"

    reference: datetime.datetime

    def __init__(self, past=None, future=None, kws_past=None, kws_future=None):

        past = 0 if past is None else past
        future = 0 if future is None else future

        kws_past = {} if kws_past is None else kws_past
        kws_future = {} if kws_future is None else kws_future
        
        self.past = abs(pd.Timedelta(past, **kws_past))
        self.future = abs(pd.Timedelta(future, **kws_future))

    @abstractmethod
    def __contains__(self, dt):
        "Check whether the datetime is in "
        reference = getattr(self, "reference", datetime.datetime.fromtimestamp(time.time()))
        start = reference - abs(self.past)
        end = reference + abs(self.future)
        return start <= dt <= end

    def rollback(self, dt):
        "Get previous interval (including currently ongoing)"
        start = dt - abs(self.past)
        start = pd.Timestamp(start)
        end = pd.Timestamp(dt)
        return pd.Interval(start, end) 

    def rollforward(self, dt):
        "Get next interval (including currently ongoing)"
        end = dt + abs(self.future)
        start = pd.Timestamp(dt)
        end = pd.Timestamp(end)
        return pd.Interval(start, end)

    def __eq__(self, other):
        "Test whether self and other are essentially the same periods"
        is_same_class = type(self) == type(other)
        if is_same_class:
            return (self.past == other.past) and (self.future == other.future)
        else:
            return False

    def __str__(self):
        if not self.future:
            return f"past {str(self.past)}"
        elif not self.past:
            return f"next {str(self.future)}"
        else:
            return f"past {str(self.past)} to next {str(self.future)}"

    def __repr__(self):
        return f"TimeDelta(past={repr(self.past)}, future={repr(self.future)})"

def all_overlap(times:List[pd.Interval]):
    return all(a.overlaps(b) for a, b in itertools.combinations(times, 2))

def get_overlapping(times):
    # Example:
    # A:    <-------------->
    # B:     <------>
    # C:         <------>
    # Out:       <-->
    starts = [interval.left for interval in times]
    ends = [interval.right for interval in times]

    start = max(starts)
    end = min(ends)
    return pd.Interval(start, end)

class All(TimePeriod):

    def __init__(self, *args):
        if any(not isinstance(arg, TimePeriod) for arg in args):
            raise TypeError("All is only supported with TimePeriods")
        elif not args:
            raise ValueError("No TimePeriods to wrap")
        self.periods = args

    def rollback(self, dt):
        intervals = [
            period.rollback(dt)
            for period in self.periods
        ]

        if all_overlap(intervals):
            # Example:
            # A:    <-------------->
            # B:     <------>
            # C:         <------>
            # Out:       <-->
            return get_overlapping(intervals)
        else:
            # A:         <---------------->
            # B:            <--->     <--->
            # C:         <------->
            # Try from:             <-|

            starts = [interval.left for interval in intervals]
            return self.rollback(max(starts) - datetime.datetime.resolution)

    def rollforward(self, dt):
        intervals = [
            period.rollforward(dt)
            for period in self.periods
        ]
        if all_overlap(intervals):
            # Example:
            # A:    <-------------->
            # B:     <------>
            # C:         <------>
            # Out:       <-->
            return get_overlapping(intervals)
        else:
            # A:          <---------------->
            # B:            <--->     <--->
            # C:                  <------->
            # Try from:         |->
            ends = [interval.right for interval in intervals]
            return self.rollforward(min(ends) + datetime.datetime.resolution)

    def __eq__(self, other):
        # self | other
        # bitwise or
        if type(self) == type(other):
            return self.periods == other.periods
        else:
            return False

class Any(TimePeriod):

    def __init__(self, *args):
        if any(not isinstance(arg, TimePeriod) for arg in args):
            raise TypeError("Any is only supported with TimePeriods")
        elif not args:
            raise ValueError("No TimePeriods to wrap")
        self.periods = args

    def rollback(self, dt):
        intervals = [
            period.rollback(dt)
            for period in self.periods
        ]

        # Example:
        # A:    <-------------->
        # B:     <------>
        # C:         <------------->
        # Out:  <------------------>

        # Example:
        # A:    <-->   
        # B:     <--->     <--->
        # C:     <------>
        # Out:  <------->

        # Example:
        # A:    <-->   
        # B:    <--->     <--->
        # C:        <----->
        # Out:  <------------->
        starts = [interval.left for interval in intervals]
        ends = [interval.right for interval in intervals]

        start = min(starts)
        end = max(ends)

        next_intervals = [
            period.rollback(start - datetime.datetime.resolution)
            for period in self.periods
        ]
        if any(pd.Interval(start, end).overlaps(interval) for interval in next_intervals):
            # Example:
            # A:    <-->   
            # B:    <--->     <--->
            # C:        <----->
            # Out:  <---------|--->
            extended = self.rollback(start - datetime.datetime.resolution)
            start = extended.left

        return pd.Interval(start, end)

    def rollforward(self, dt):
        intervals = [
            period.rollforward(dt)
            for period in self.periods
        ]

        starts = [interval.left for interval in intervals]
        ends = [interval.right for interval in intervals]

        start = min(starts)
        end = max(ends)

        next_intervals = [
            period.rollforward(end + datetime.datetime.resolution)
            for period in self.periods
        ]

        if any(pd.Interval(start, end).overlaps(interval) for interval in next_intervals):
            # Example:
            # A:    <-->   
            # B:    <--->     <--->
            # C:        <----->
            # Out:  <---------|--->
            extended = self.rollforward(end + datetime.datetime.resolution)
            end = extended.right

        return pd.Interval(start, end)

    def __eq__(self, other):
        # self | other
        # bitwise or
        if type(self) == type(other):
            return self.periods == other.periods
        else:
            return False

class StaticInterval(TimePeriod):
    """Inverval that is fixed in specific datetimes."""

    def __init__(self, start=None, end=None):
        self.start = start if start is not None else self.min
        self.end = end if end is not None else self.max

    def rollback(self, dt):
        dt = pd.Timestamp(dt)
        start = pd.Timestamp(self.start)
        if start > dt:
            # The actual interval is in the future
            return pd.Interval(self.min, self.min)
        return pd.Interval(start, dt)

    def rollforward(self, dt):
        dt = pd.Timestamp(dt)
        end = pd.Timestamp(self.end)
        if end < dt:
            # The actual interval is already gone
            return pd.Interval(self.max, self.max, closed="both")
        return pd.Interval(dt, end, closed="both")

    @property
    def is_max_interval(self):
        return (self.start == self.min) and (self.end == self.max)
