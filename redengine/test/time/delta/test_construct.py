
import pytest
import pandas as pd
import numpy as np
from redengine.time import (
    TimeDelta, TimeOfDay
)

@pytest.mark.parametrize(
    "offset,expected",
    [
        pytest.param(
            "10:20:30",
            pd.Timedelta(hours=10, minutes=20, seconds=30),
            id="String"),
    ],
)
def test_construct(offset, expected):
    time = TimeDelta(offset)
    assert expected == time.past

@pytest.mark.parametrize(
    "kwargs,exc",
    [
        pytest.param(
            {"past": np.nan},
            TypeError,
            id="Invalid past"),
        pytest.param(
            {"future": np.nan},
            TypeError,
            id="Invalid future"),
    ],
)
def test_fail(kwargs, exc):
    with pytest.raises(exc):
        time = TimeDelta(**kwargs)

def test_equal():
    assert TimeDelta("2 days") == TimeDelta("2 days")
    assert not (TimeDelta("2 days") == TimeDelta("3 days"))
    assert not (TimeDelta("2 days") == TimeOfDay("10:00", "12:00"))

def test_repr():
    assert str(TimeDelta("2 days")) == 'past 2 days 00:00:00'
    assert str(TimeDelta(future="2 days")) == 'next 2 days 00:00:00'
    assert str(TimeDelta(past="1 days", future="2 days")) == 'past 1 days 00:00:00 to next 2 days 00:00:00'
    assert repr(TimeDelta("2 days")) == "TimeDelta(past=Timedelta('2 days 00:00:00'), future=Timedelta('0 days 00:00:00'))"