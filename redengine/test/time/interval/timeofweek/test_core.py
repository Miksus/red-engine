
import pytest
import pandas as pd

from redengine.time.interval import (
    TimeOfWeek
)

NS_IN_SECOND = 1e+9
NS_IN_MINUTE = 1e+9 * 60
NS_IN_HOUR   = 1e+9 * 60 * 60
NS_IN_DAY    = 1e+9 * 60 * 60 * 24
NS_IN_WEEK   = 1e+9 * 60 * 60 * 24 * 7

# TimeOfWeek
# Year 2024 was chosen as it starts on monday
@pytest.mark.parametrize(
    "dt,string,ns",
    [
        # Regular
        pytest.param(
            pd.Timestamp("2024-01-01 00:00:00"),
            "Mon 00:00:00",
            0,
            id="Beginning"),
        pytest.param(
            pd.Timestamp("2024-01-07 23:59:59.999999000"),
            "Sun 23:59:59.999999000",
            604799999999000.0,
            id="Ending"),
    ],
)
def test_anchor_equal(dt, string, ns):
    time = TimeOfWeek(None, None)
    assert time.anchor_dt(dt) == time.anchor_str(string) == ns


@pytest.mark.parametrize(
    "start,end,start_ns,end_ns",
    [
        # Regular
        pytest.param(
            "Mon 00:00:00",
            "Sun 23:59:59.999999000",
            0, NS_IN_WEEK - 1 - 999, # datetime stuff are often microsecond accuracy
            id="Strings: full"),
        pytest.param(
            # From Tue 00:00 to Wed 23:59:59.000 ()
            "Tue",
            "Wed", # 
            NS_IN_DAY, NS_IN_DAY * 3 - 1,
            id="Strings: minimal"),
    ],
)
def test_construct(start, end, start_ns, end_ns):
    time = TimeOfWeek(start, end)
    assert time._start == start_ns
    assert time._end == end_ns
