
import pytest
from redengine.time.interval import (
    TimeOfDay,
    TimeOfMonth,
    TimeOfWeek
)

NS_IN_SECOND = 1e+9
NS_IN_MINUTE = 1e+9 * 60
NS_IN_HOUR   = 1e+9 * 60 * 60
NS_IN_DAY    = 1e+9 * 60 * 60 * 24

def pytest_generate_tests(metafunc):
    if metafunc.cls is not None:

        method_name = metafunc.function.__name__
        cls = metafunc.cls
        params = []
        if method_name == "test_closed":
            params = cls.scen_closed
        elif method_name == "test_open":
            return
        elif method_name == "test_open_left":
            params = cls.scen_open_left
        elif method_name == "test_open_right":
            params = cls.scen_open_right
        elif method_name == "test_time_point":
            params = cls.scen_time_point
        else:
            return
        
        argnames = [arg for arg in metafunc.fixturenames if arg in ('start', 'end', "expected_start", "expected_end", "time_point")]

        idlist = []
        argvalues = []
        argvalues = []
        for scen in params:
            idlist.append(scen.pop("id", f'{scen.get("start")}, {scen.get("end")}'))
            argvalues.append(tuple(scen[name] for name in argnames))
        metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")

class ConstructTester:

    def test_closed(self, start, end, expected_start, expected_end):
        time = self.cls(start, end)
        assert expected_start == time._start
        assert expected_end == time._end

    def test_open(self):
        time = self.cls(None, None)
        assert 0 == time._start
        assert self.max_ns == time._end

    def test_open_left(self, end, expected_end, **kwargs):
        time = self.cls(None, end)
        assert 0 == time._start
        assert expected_end == time._end

    def test_open_right(self, start, expected_start, **kwargs):
        time = self.cls(start, None)
        assert expected_start == time._start
        assert self.max_ns == time._end

    def test_time_point(self, start, expected_start, expected_end, **kwargs):
        time = self.cls(start, time_point=True)
        assert expected_start == time._start
        assert expected_end == time._end

class TestTimeOfDay(ConstructTester):

    cls = TimeOfDay

    max_ns = 24 * NS_IN_HOUR - 1

    scen_closed = [
        {
            "start": "10:00",
            "end": "12:00",
            "expected_start": 10 * NS_IN_HOUR,
            "expected_end": 12 * NS_IN_HOUR,
        }
    ]

    scen_open_left = [
        {
            "end": "12:00",
            "expected_end": 12 * NS_IN_HOUR
        }
    ]
    scen_open_right = [
        {
            "start": "12:00",
            "expected_start": 12 * NS_IN_HOUR
        }
    ]
    scen_time_point = [
        {
            "start": "12:00",
            "expected_start": 12 * NS_IN_HOUR,
            "expected_end": 13 * NS_IN_HOUR - 1,
        }
    ]


class TestTimeOfWeek(ConstructTester):

    cls = TimeOfWeek

    max_ns = 7 * NS_IN_DAY - 1

    scen_closed = [
        {
            # Spans from Tue 00:00:00 to Wed 23:59:59 999
            "start": "Tue",
            "end": "Wed",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 3 * NS_IN_DAY - 1,
        },
        {
            # Spans from Tue 00:00:00 to Wed 23:59:59 999
            "start": "Tuesday",
            "end": "Wednesday",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 3 * NS_IN_DAY - 1,
        }
    ]

    scen_open_left = [
        {
            "end": "Tue",
            "expected_end": 2 * NS_IN_DAY - 1 # Tuesday 23:59:59 ...
        }
    ]
    scen_open_right = [
        {
            "start": "Tue",
            "expected_start": 1 * NS_IN_DAY # Tuesday 00:00:00
        }
    ]
    scen_time_point = [
        {
            "start": "Tue",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 2 * NS_IN_DAY - 1,
        }
    ]


class TestTimeOfMonth(ConstructTester):

    cls = TimeOfMonth

    max_ns = 31 * NS_IN_DAY - 1

    scen_closed = [
        {
            "start": "2.",
            "end": "3.",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 3 * NS_IN_DAY - 1,
        },
        {
            "start": "2nd",
            "end": "4th",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 4 * NS_IN_DAY - 1,
        },
    ]

    scen_open_left = [
        {
            "end": "3.",
            "expected_end": 3 * NS_IN_DAY - 1 
        }
    ]
    scen_open_right = [
        {
            "start": "2.",
            "expected_start": 1 * NS_IN_DAY 
        }
    ]
    scen_time_point = [
        {
            "start": "2.",
            "expected_start": 1 * NS_IN_DAY,
            "expected_end": 2 * NS_IN_DAY - 1,
        }
    ]
