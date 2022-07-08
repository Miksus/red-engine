
"""
Test whether a time is inside of an interval.
Also tests conditions.IsPeriod that is essentially a 
wrapper for periods.
"""

import pytest
import pandas as pd

from redengine.time.interval import (
    TimeOfHour,
    TimeOfDay, 
    TimeOfWeek,
    TimeOfMonth,
    TimeOfYear,
)
from redengine.conditions import IsPeriod


true_cases = [
    # TimeOfHour
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:30",
        "start": "15:00",
        "end": "45:00",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:30",
        "start": "1 quarter",
        "end": "3 quarter",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:05",
        "start": "45:00",
        "end": "15:00",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:55",
        "start": "45:00",
        "end": "15:00",
    },

    # TimeOfDay
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 10:00",
        "start": "09:00",
        "end": "12:00",
        "id": "In period"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 23:00",
        "start": "22:00",
        "end": "02:00",
        "id": "In period overnight before mid-night"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 01:00",
        "start": "22:00",
        "end": "02:00",
        "id": "In period overnight after mid-night"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 09:00",
        "start": "10:00",
        "end": "10:00",
        "id": "Full left"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 11:00",
        "start": "10:00",
        "end": "10:00",
        "id": "Full right"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 10:00",
        "start": "10:00",
        "end": "10:00",
        "id": "Full mid"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 10:00",
        "start": None,
        "end": None,
        "id": "Full"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 10:30",
        "start": "10:00",
        "end": None,
        "time_point": True,
        "id": "at"
    },

    # TimeOfWeek
    {
        "cls": TimeOfDay,
        "dt": "2024-01-01 01:00", # 2024 starts from monday
        "start": "Mon",
        "end": "Wed",
    },
    {
        "cls": TimeOfDay,
        "dt": "2024-01-03 01:00", # 2024 starts from monday
        "start": "Mon",
        "end": "Wed",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-02 01:00", # 2024 starts from monday
        "start": "Tue",
        "end": "Tue",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-07 01:00", # 2024 starts from monday
        "start": "Tue",
        "end": None,
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-07 01:00", # 2024 starts from monday
        "start": None,
        "end": None,
    },

    # TimeOfMonth
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-05 01:00",
        "start": "5th",
        "end": "10th",
    },
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-10 01:00",
        "start": "5th",
        "end": "10th",
    },

    # TimeOfYear
    {
        "cls": TimeOfYear,
        "dt": "2024-01-01 01:00",
        "start": "Jan",
        "end": "Feb",
    },
    {
        "cls": TimeOfYear,
        "dt": "2024-02-29 23:00",
        "start": "Jan",
        "end": "Feb",
    },
]

false_cases = [
    # TimeOfHour
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:14",
        "start": "15:00",
        "end": "45:00",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:46",
        "start": "15:00",
        "end": "45:00",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:14",
        "start": "1 quarter",
        "end": "3 quarter",
    },
    {
        "cls": TimeOfHour,
        "dt": "2020-01-01 10:46",
        "start": "1 quarter",
        "end": "3 quarter",
    },

    # TimeOfDay
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 08:00",
        "start": "09:00",
        "end": "12:00",
        "id": "Before period"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 13:00",
        "start": "09:00",
        "end": "12:00",
        "id": "After period"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 21:00",
        "start": "22:00",
        "end": "02:00",
        "id": "Before period overnight"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 03:00",
        "start": "22:00",
        "end": "02:00",
        "id": "After period overnight"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 09:59",
        "start": "10:00",
        "end": None,
        "time_point": True,
        "id": "left of at"
    },
    {
        "cls": TimeOfDay,
        "dt": "2020-01-01 11:00",
        "start": "10:00",
        "end": None,
        "time_point": True,
        "id": "right of at"
    },

    # IsTimeOfWeek
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-01 23:59:59.999", # 2024 starts from monday
        "start": "Tue",
        "end": "Wed",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-04 00:00:00.001", # 2024 starts from monday
        "start": "Tue",
        "end": "Wed",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-01 23:59:59.999", # 2024 starts from monday
        "start": "Tue",
        "end": "Tue",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-03 01:00", # 2024 starts from monday
        "start": "Tue",
        "end": "Tue",
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-01 01:00", # 2024 starts from monday
        "start": "Tue",
        "end": None,
    },
    {
        "cls": TimeOfWeek,
        "dt": "2024-01-06 01:00", # 2024 starts from monday
        "start": None,
        "end": "Fri",
    },

    # TimeOfMonth
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-04 01:00",
        "start": "5th",
        "end": "10th",
    },
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-11 01:00",
        "start": "5th",
        "end": "10th",
    },
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-10 12:30:00.001",
        "start": "5th",
        "end": "10th 12:30:00",
    },
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-28 23:59:59.999",
        "start": "29th",
        "end": "5th",
    },
    {
        "cls": TimeOfMonth,
        "dt": "2024-01-06 00:00:00",
        "start": "29th",
        "end": "5th",
    },

    # TimeOfYear
    {
        "cls": TimeOfYear,
        "dt": "2024-01-31 23:59:59.999",
        "start": "Feb",
        "end": "Jul",
    },
    {
        "cls": TimeOfYear,
        "dt": "2024-08-01 00:00:00",
        "start": "Feb",
        "end": "Jul",
    },
]

def _to_pyparams(cases):
    return pytest.mark.parametrize(
        "dt,start,end,cls,time_point",
        [
            pytest.param(
                case["dt"],
                case["start"],
                case["end"],
                case["cls"],
                case.get('time_point', None),
                id=f"{case['cls'].__name__}({case['start']}, {case['end']}) --> {case['dt']}{' with time_point' if 'time_point' in case else ''}"
            )
            for case in cases
        ]
    )

@_to_pyparams(true_cases)
def test_in(dt, start, end, cls, time_point):
    dt = pd.Timestamp(dt)
    time = cls(start, end, time_point=time_point)

    assert dt in time

@_to_pyparams(false_cases)
def test_not(dt, start, end, cls, time_point):
    dt = pd.Timestamp(dt)
    time = cls(start, end, time_point=time_point)
    
    assert dt not in time

# Test conditions
@_to_pyparams(true_cases)
def test_true(dt, start, end, cls, time_point, mock_datetime_now):
    mock_datetime_now(dt)
    cond = IsPeriod(cls(start, end, time_point=time_point))
    assert bool(cond)

@_to_pyparams(false_cases)
def test_false(dt, start, end, cls, time_point, mock_datetime_now):
    mock_datetime_now(dt)
    cond = IsPeriod(cls(start, end, time_point=time_point))
    assert not bool(cond)