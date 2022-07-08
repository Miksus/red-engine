
import pytest

from redengine.conditions import (
    true, false, ParamExists, IsPeriod,
    Any, All
)
from redengine.core.condition import Statement, Comparable, Historical

from redengine.time import TimeDelta

def test_true():
    assert bool(true)

def test_false():
    assert not bool(false)

@pytest.mark.parametrize(
    "params,make_cond,expected",
    [
        pytest.param(
            {"mode": "test", "state": "right"},
            lambda: ParamExists(mode="test", state="right"),
            True, id="Dict, true"
        ),
        pytest.param(
            {"mode": "test", "state": "right"},
            lambda: ParamExists(mode="test", state="wrong"),
            False, id="Dict, false (wrong value)"
        ),
        pytest.param(
            {"mode": "test", "state": "right"},
            lambda: ParamExists(mode="test", stuff="right"),
            False, id="Dict, false (missing key)"
        ),
        pytest.param(
            {"mode": "test", "state": "right"},
            lambda: ParamExists("mode"),
            True, id="Tuple, true"
        ),
        pytest.param(
            {"mode": "test", "state": "right"},
            lambda: ParamExists("stuff"),
            False, id="Tuple, false (missing key)"
        ),
        pytest.param(
            {"mode": "test", "feel": "good", "state": "right", "distance": "short", "world": "this"},
            lambda: ParamExists("mode", "feel", state="right", distance="short"),
            True, id="Multi, true"
        ),
        pytest.param(
            {},
            lambda: ParamExists("mode", "feel", state="right", distance="short"),
            False, id="Multi, false (empty)"
        ),
    ]
)
def test_params(session, params, make_cond, expected):
    
    session.parameters.update(params)
    cond = make_cond()
    if expected:
        assert bool(cond)
    else:
        assert not bool(cond)

def test_parameter_exists(session):
    cond = ParamExists(x="yes", y="yes")
    assert not bool(cond)

    session.parameters["x"] = "yes"
    assert not bool(cond)

    session.parameters["y"] = "yes"
    assert bool(cond)

    session.parameters["y"] = "no"
    assert not bool(cond)


# Test no unexpected errors in all
@pytest.mark.parametrize("cls", set(Statement.__subclasses__() + Comparable.__subclasses__() + Historical.__subclasses__()))
def test_magic_noerror(cls):
    if cls.__name__ in ('TaskSucceeded', 'DependFinish', 'TaskTerminated', 'TaskFinished', 'TaskFailed', 'DependFailure', 'TaskStarted', 'DependSuccess', 'TaskInacted', 'TaskRunning'):
        pytest.skip("Initing requires task as argument")
    str(cls())

@pytest.mark.parametrize("get_cond,exc",
    [
        pytest.param(lambda: IsPeriod(TimeDelta("2 hours")), AttributeError, id="IsPeriod with timedelta")
    ]
)
def test_fail(get_cond,exc):
    with pytest.raises(exc):
        get_cond()

@pytest.mark.parametrize("obj,string,represent", 
    [
        pytest.param(
            All(true, false), 
            "(true & false)", 
            "All(true, false)", 
            id="All"),
        pytest.param(
            Any(true, false), 
            "(true | false)", 
            "Any(true, false)", 
            id="Any")
    ]
)
def test_representation(obj, string, represent):
    assert str(obj) == string
    assert repr(obj) == represent