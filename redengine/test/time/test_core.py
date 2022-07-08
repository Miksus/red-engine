
import pytest
import pandas as pd

from redengine.time.interval import (
    TimeOfHour,
    TimeOfDay, 
    TimeOfWeek,
    TimeOfMonth,
    TimeOfYear,
)
from redengine.time import All, Any

def test_equal():
    assert not (TimeOfHour("10:00") == TimeOfHour("11:00"))
    assert TimeOfHour("10:00") == TimeOfHour("10:00")
    assert (TimeOfHour("10:00", "12:00") & TimeOfHour("11:00", "13:00")) == (TimeOfHour("10:00", "12:00") & TimeOfHour("11:00", "13:00"))
    assert (TimeOfHour("10:00", "12:00") | TimeOfHour("11:00", "13:00")) == (TimeOfHour("10:00", "12:00") | TimeOfHour("11:00", "13:00"))

def test_and():
    time = TimeOfHour("10:00", "14:00") & TimeOfHour("09:00", "12:00")
    assert time == All(TimeOfHour("10:00", "14:00"), TimeOfHour("09:00", "12:00"))

def test_any():
    time = TimeOfHour("10:00", "14:00") | TimeOfHour("09:00", "12:00")
    assert time == Any(TimeOfHour("10:00", "14:00"), TimeOfHour("09:00", "12:00"))