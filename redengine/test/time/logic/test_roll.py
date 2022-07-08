
import pytest
import pandas as pd

from redengine.core.time.base import (
    All, Any
)
from redengine.time.interval import TimeOfDay

@pytest.mark.parametrize(
    "dt,periods,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 07:00:00"),
            [
                TimeOfDay("08:00", "18:00"),
                TimeOfDay("10:00", "14:00"),
                TimeOfDay("12:00", "16:00"),
            ],
            pd.Timestamp("2020-01-01 12:00:00"), pd.Timestamp("2020-01-01 14:00:00"),
            id="Left from interval"),
    ],
)
def test_rollforward_all(dt, periods, roll_start, roll_end):
    time = All(*periods)

    interval = time.rollforward(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right

@pytest.mark.parametrize(
    "dt,periods,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-02 07:00:00"),
            [
                TimeOfDay("08:00", "18:00"),
                TimeOfDay("10:00", "14:00"),
                TimeOfDay("12:00", "16:00"),
            ],
            pd.Timestamp("2020-01-01 12:00:00"), pd.Timestamp("2020-01-01 14:00:00"),
            id="Left from interval"),
    ],
)
def test_rollback_all(dt, periods, roll_start, roll_end):
    time = All(*periods)

    interval = time.rollback(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right

@pytest.mark.parametrize(
    "dt,periods,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 07:00:00"),
            [
                TimeOfDay("08:00", "18:00"),
                TimeOfDay("10:00", "14:00"),
                TimeOfDay("12:00", "16:00"),
            ],
            pd.Timestamp("2020-01-01 08:00:00"), pd.Timestamp("2020-01-01 18:00:00"),
            id="Left from interval"),
    ],
)
def test_rollforward_any(dt, periods, roll_start, roll_end):
    time = Any(*periods)

    interval = time.rollforward(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right

@pytest.mark.parametrize(
    "dt,periods,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-02 07:00:00"),
            [
                TimeOfDay("08:00", "18:00"),
                TimeOfDay("10:00", "14:00"),
                TimeOfDay("12:00", "16:00"),
            ],
            pd.Timestamp("2020-01-01 08:00:00"), pd.Timestamp("2020-01-01 18:00:00"),
            id="Left from interval"),
    ],
)
def test_rollback_any(dt, periods, roll_start, roll_end):
    time = Any(*periods)

    interval = time.rollback(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right