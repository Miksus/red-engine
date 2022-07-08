
import pytest

from redengine.conditions import (
    true, false, 
    All, Any, Not
)

@pytest.mark.parametrize("actual,expected",
    [
        pytest.param(
            lambda: (true & (true & true)),
            lambda: All(true, true, true),
            id="All"
        ),
        pytest.param(
            lambda: (true | (true | true)),
            lambda: Any(true, true, true),
            id="Any"
        ),
        pytest.param(
            lambda: Not(Not(Not(true))),
            lambda: Not(Not(Not(true))),
            id="Not"
        ),
        pytest.param(
            lambda: (true & true) & (false | false),
            lambda: All(All(true, true), Any(false, false)),
            id="Complex"
        ),
    ]
)
def test_nested(actual, expected):
    expected = expected()
    actual = actual()
    assert expected == actual