
import pytest
from datetime import datetime

from redengine.time.interval import (
    TimeOfWeek
)

# TimeOfWeek
# Year 2024 was chosen as it starts on monday
@pytest.mark.parametrize(
    "dt,start,end",
    [
        # Regular
        pytest.param(
            datetime(2024, 1, 2, 10, 00),
            "Tue 10:00", "Sat 12:00",
            id="Left of interval"),
        pytest.param(
            datetime(2024, 1, 6, 12, 00),
            "Tue 10:00", "Sat 12:00",
            id="Right of interval"),
        pytest.param(
            datetime(2024, 1, 4, 11, 00),
            "Tue 10:00", "Sat 12:00",
            id="Middle of interval"),

        # Over weekend
        pytest.param(
            datetime(2024, 1, 6, 10, 00),
            "Sat 10:00", "Tue 12:00",
            id="Left of over weekend interval"),
        pytest.param(
            datetime(2024, 1, 9, 12, 00),
            "Sat 10:00", "Tue 12:00",
            id="Right of over weekend interval"),
        pytest.param(
            datetime(2024, 1, 7, 23, 59, 59, 999999),
            "Sat 10:00", "Tue 12:00",
            id="Middle left of over weekend interval"),
        pytest.param(
            datetime(2024, 1, 8, 00, 00),
            "Sat 10:00", "Tue 12:00",
            id="Middle right of over weekend interval"),

        # Full Cycle
        pytest.param(
            datetime(2024, 1, 1, 00, 00),
            None, None,
            id="Full interval"),
        pytest.param(
            datetime(2024, 1, 2, 00, 00),
            "Tue", "Tue",
            id="Joint of full interval"),
        pytest.param(
            datetime(2024, 1, 1, 00, 00),
            "Tue 00:00", "Tue 00:00",
            id="Right of full interval"),
        pytest.param(
            datetime(2024, 1, 6, 00, 00),
            "Tue 00:00", "Tue 00:00",
            id="Left of full interval"),
    ],
)
def test_in(start, end, dt):
    time = TimeOfWeek(start, end)
    assert dt in time


@pytest.mark.parametrize(
    "dt,start,end",
    [
        # Regular
        pytest.param(
            datetime(2024, 1, 1, 0, 0),
            "Tue 10:00", "Sat 12:00",
            id="Left from interval"),
        pytest.param(
            datetime(2024, 1, 7, 14, 00, 00, 1),
            "Tue 10:00", "Sat 12:00",
            id="Right from interval"),

        # Over weekend
        pytest.param(
            datetime(2024, 1, 6, 9, 59, 59, 999999),
            "Sat 10:00", "Tue 12:00",
            id="Left from over weekend interval"),
        pytest.param(
            datetime(2024, 1, 9, 12, 1, 00),
            "Sat 10:00", "Tue 12:00",
            id="Right from over weekend interval"),
    ],
)
def test_not_in(start, end, dt):
    time = TimeOfWeek(start, end)
    assert dt not in time