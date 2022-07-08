
import pytest
import pandas as pd
from redengine.core.time import (
    TimeDelta
)

@pytest.mark.parametrize(
    "dt,past,future,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            None, None,
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 10:00:00"),
            id="No roll"),
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            None, "1:20:30",
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 11:20:30"),
            id="Regular"),
    ],
)
def test_rollforward(dt, past, future, roll_start, roll_end):
    time = TimeDelta(past, future)

    interval = time.rollforward(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right


@pytest.mark.parametrize(
    "dt,past,future,roll_start,roll_end",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            None, None,
            pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 10:00:00"),
            id="No roll"),
        pytest.param(
            pd.Timestamp("2020-01-01 10:00:00"),
            "1:20:30", None,
            pd.Timestamp("2020-01-01 08:39:30"), pd.Timestamp("2020-01-01 10:00:00"),
            id="Regular"),
    ],
)
def test_rollback(dt, past, future, roll_start, roll_end):
    time = TimeDelta(past, future)

    interval = time.rollback(dt)
    assert roll_start == interval.left
    assert roll_end == interval.right


