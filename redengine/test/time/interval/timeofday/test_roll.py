
import pytest
import pandas as pd

from redengine.time.interval import (
    TimeOfDay
)

@pytest.mark.parametrize(
    "dt,start,end,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 12:00:00"),
            id="Left of interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 12:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 12:00:00"), pd.Timestamp("2020-01-01 12:00:00"),
            id="Right of interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 11:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 11:00:00"), pd.Timestamp("2020-01-01 12:00:00"),
            id="Middle of interval"),

        # Overnight
        pytest.param(
            pd.Timestamp("2020-01-01 22:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 22:00:00"), pd.Timestamp("2020-01-02 02:00:00"),
            id="Left of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 02:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 02:00:00"), pd.Timestamp("2020-01-01 02:00:00"),
            id="Right of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 23:59:59.999999"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 23:59:59.999999"), pd.Timestamp("2020-01-02 02:00:00"),
            id="Middle left of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 00:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 00:00:00"), pd.Timestamp("2020-01-01 02:00:00"),
            id="Middle right of overnight interval"),

        # Full Cycle
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-02 10:00:00"),
            id="Joint of full interval", marks=pytest.mark.xfail),
        pytest.param(
            pd.Timestamp("2020-01-01 12:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2020-01-01 12:00:00"), pd.Timestamp("2020-01-02 10:00:00"),
            id="Right of full interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 09:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2020-01-01 09:00:00"), pd.Timestamp("2020-01-01 10:00:00"),
            id="Left of full interval"),
    ],
)
def test_rollforward(start, end, dt, roll_start, roll_end):
    time = TimeOfDay(start, end)

    interval = time.rollforward(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right


@pytest.mark.parametrize(
    "dt,start,end,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 10:00:00"),
            id="Left of interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 12:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 12:00:00"),
            id="Right of interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 11:00:00"),
            "10:00", "12:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 11:00:00"),
            id="Middle of interval"),

        # Overnight
        pytest.param(
            pd.Timestamp("2020-01-01 22:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 22:00:00"), pd.Timestamp("2020-01-01 22:00:00"),
            id="Left of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 02:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2019-12-31 22:00:00"), pd.Timestamp("2020-01-01 02:00:00"),
            id="Right of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 23:59:59.999999"),
            "22:00", "02:00",
            pd.Timestamp("2020-01-01 22:00:00"), pd.Timestamp("2020-01-01 23:59:59.999999"),
            id="Middle left of overnight interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 00:00:00"),
            "22:00", "02:00",
            pd.Timestamp("2019-12-31 22:00:00"), pd.Timestamp("2020-01-01 00:00:00"),
            id="Middle right of overnight interval"),

        # Full Cycle
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2019-12-31 10:00:00"), pd.Timestamp("2020-01-01 10:00:00"),
            id="Joint of full interval", marks=pytest.mark.xfail),
        pytest.param(
            pd.Timestamp("2020-01-01 12:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 12:00:00"),
            id="Right of full interval"),
        pytest.param(
            pd.Timestamp("2020-01-01 09:00:00"),
            "10:00", "10:00",
            pd.Timestamp("2019-12-31 10:00:00"), pd.Timestamp("2020-01-01 09:00:00"),
            id="Left of full interval"),
    ],
)
def test_rollback(start, end, dt, roll_start, roll_end):
    time = TimeOfDay(start, end)

    interval = time.rollback(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right


