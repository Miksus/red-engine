
import pytest

from redengine.core import Parameters
from redengine.args import Private

@pytest.mark.parametrize(
    "a,b,union",
    [
        pytest.param(
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: Parameters({"c": 3, "d": 4}),
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Parameters | Parameters"),
        pytest.param(
            lambda: Parameters({"a": 0, "b": Private(1)}),
            lambda: Parameters({"c": 3, "d": Private(4)}),
            lambda: Parameters({"a": 0, "b": Private(1), "c": 3, "d": Private(4)}),
            id="Parameters | Parameters, with private"),
        pytest.param(
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: {"c": 3, "d": 4},
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Parameters | Dict"),
        pytest.param(
            lambda: {"c": 3, "d": 4},
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Dict | Parameters", marks=pytest.mark.xfail),
    ],
)
def test_union(a, b, union):
    a = a()
    b = b()
    union = union()
    actual_union = a | b
    assert union == actual_union


@pytest.mark.parametrize(
    "a,b,union",
    [
        pytest.param(
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: Parameters({"c": 3, "d": 4}),
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Parameters | Parameters"),
        pytest.param(
            lambda: Parameters({"a": 0, "b": Private(1)}),
            lambda: Parameters({"c": 3, "d": Private(4)}),
            lambda: Parameters({"a": 0, "b": Private(1), "c": 3, "d": Private(4)}),
            id="Parameters | Parameters, with private"),
        pytest.param(
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: {"c": 3, "d": 4},
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Parameters | Dict"),
        pytest.param(
            lambda: {"c": 3, "d": 4},
            lambda: Parameters({"a": 0, "b": 1}),
            lambda: Parameters({"a": 0, "b": 1, "c": 3, "d": 4}),
            id="Dict | Parameters", marks=pytest.mark.xfail),
    ],
)
def test_update(a, b, union):
    a = a()
    b = b()
    union = union()
    a.update(b)
    assert union.materialize() == a.materialize()