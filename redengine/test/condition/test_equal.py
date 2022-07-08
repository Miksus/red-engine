
import pytest

from redengine.conditions import (
    AlwaysTrue, AlwaysFalse, 
    All, Any, Not,
    TaskFinished, TaskRunning,
)

@pytest.mark.parametrize(
    "get_cond",
    [
        pytest.param(lambda: AlwaysTrue(), id="AlwaysTrue"),
        pytest.param(lambda: AlwaysFalse(), id="AlwaysFalse"),
        pytest.param(lambda: All(AlwaysTrue(), AlwaysTrue()), id="All"),
        pytest.param(lambda: Any(AlwaysTrue(), AlwaysTrue()), id="Any"),
        pytest.param(lambda: Not(AlwaysTrue()), id="Not"),
        pytest.param(lambda: Not(Any(AlwaysTrue(), All(AlwaysTrue(), AlwaysTrue()))), id="Nested"),
        pytest.param(lambda: TaskFinished(task="mytask"), id="Statement (historical & comparable)"),
        pytest.param(lambda: TaskRunning(task="mytask"), id="Statement (not historical & not comparable)"),
    ],
)
def test_equal(get_cond):
    assert get_cond() == get_cond()


@pytest.mark.parametrize(
    "get_a,get_b",
    [
        pytest.param(
            lambda: AlwaysTrue(), 
            lambda: AlwaysFalse(), 
            id="AlwaysTrue/AlwaysFalse"
        ),
        pytest.param(
            lambda: All(AlwaysTrue(), AlwaysTrue()), 
            lambda: Any(AlwaysTrue(), AlwaysTrue()), 
            id="All/Any"
        ),
        pytest.param(
            lambda: AlwaysTrue(), 
            lambda: Not(AlwaysTrue()), 
            id="Not"
        ),
        pytest.param(
            lambda: TaskFinished(task="mytask"), 
            lambda: TaskFinished(task="another task"), 
            id="TaskFinished"
        ),
    ],
)
def test_equal_not(get_a, get_b):
    assert not (get_a() == get_b())