
from redengine.parse import parse_condition
from redengine.conditions import (
    AlwaysTrue, AlwaysFalse, 
    Not,
)
import pytest

@pytest.mark.parametrize(
    "cond_str,expected",
    [
        pytest.param(
            "always true", 
            AlwaysTrue(),
            id="AlwaysTrue"),

        pytest.param(
            "always false", 
            AlwaysFalse(),
            id="AlwaysFalse"),

        pytest.param(
            "always true & always true", 
            AlwaysTrue() & AlwaysTrue(),
            id="All"),
        pytest.param(
            "always true | always true", 
            AlwaysTrue() | AlwaysTrue(),
            id="Any"),
        pytest.param(
            "~always true", 
            Not(AlwaysTrue()),
            id="Not"),

        pytest.param(
            "~~always true", 
            ~~AlwaysTrue(),
            id="Nested Not"),

        pytest.param(
            "~(always true)", 
            ~AlwaysTrue(),
            id="Closured Not"),

        pytest.param(
            "~(always true & always true)", 
            ~(AlwaysTrue() & AlwaysTrue()),
            id="All in Not"),

        pytest.param(
            "~(always true | always true)", 
            ~(AlwaysTrue() | AlwaysTrue()),
            id="Any in Not"),

        pytest.param(
            "~always true | ~always true & ~always true", 
            ~AlwaysTrue() | ~AlwaysTrue() & ~AlwaysTrue(),
            id="Multiple Not"),

        pytest.param(
            "always true & (always true | always true & (always true | always true))", 
            AlwaysTrue() & (AlwaysTrue() | AlwaysTrue() & (AlwaysTrue() | AlwaysTrue())),
            id="Deeply nested"),
        pytest.param(
            "~always true & ~~(always true | ~always true & ~(~~always true | ~always true))", 
            ~AlwaysTrue() & ~~(AlwaysTrue() | ~AlwaysTrue() & ~(~~AlwaysTrue() | ~AlwaysTrue())),
            id="Deeply nested Not"),

        pytest.param(
            "", 
            AlwaysFalse(),
            id="Empty", marks=pytest.mark.xfail),
    ],
)
def test_string(cond_str, expected):
    cond = parse_condition(cond_str)
    assert cond == expected


@pytest.mark.parametrize(
    "cond_str",
    [
        pytest.param(
            "daily between 20:00 and 23:59", 
            id="daily between"),
    ],
)
def test_string_matching(cond_str):
    cond = parse_condition(cond_str)