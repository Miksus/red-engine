
import pytest
import redengine
from redengine.args import FuncArg

from redengine.core import Parameters
from redengine.args import Private
from redengine.parameters import FuncParam

@pytest.mark.parametrize(
    "get_param,mater,repr",
    [
        pytest.param(
            lambda: Parameters({"x": 0, "y": 1}),
            {"x": 0, "y": 1},
            {"x": 0, "y": 1},
            id="Dict"),
        pytest.param(
            lambda: Parameters(x=0, y=1),
            {"x": 0, "y": 1},
            {"x": 0, "y": 1},
            id="Kwargs"),
        pytest.param(
            lambda: Parameters(password="pwd1234", user_id="myself", type_=Private),
            {"password": "pwd1234", "user_id": "myself"},
            {"password": "*****", "user_id": "*****"},
            id="Dict as private"),
    ],
)
def test_contruct(get_param, mater, repr):
    params = get_param()
    assert mater == params.materialize(task="mytask")
    assert repr == params.materialize()
    assert repr == dict(**params)


def test_from_func(session):

    assert "myparam" not in session.parameters
    assert "a_param" not in session.parameters

    @session.parameters.param_func
    def myparam():
        return 5

    assert "myparam" in session.parameters
    assert session.parameters.materialize() == {"myparam": 5}
    session.parameters.clear()

    @session.parameters.param_func(key="a_param")
    def myparam2(session):
        assert "a_param" in session.parameters.keys()
        return 5

    assert "a_param" in session.parameters
    assert session.parameters.materialize() == {"a_param": 5}

def test_func_param(session:redengine.Session):
    @FuncParam()
    def my_param():
        return 5
    
    assert my_param() == 5
    assert 'my_param' in session.parameters
    assert isinstance(session.parameters._params['my_param'], FuncArg)
    assert session.parameters['my_param'] == 5
    assert session.parameters._params['my_param'].func is my_param

def test_func_param_named(session:redengine.Session):
    @FuncParam(name="a_param")
    def my_param():
        return 5
    
    assert my_param() == 5
    assert 'a_param' in session.parameters
    assert isinstance(session.parameters._params['a_param'], FuncArg)
    assert session.parameters['a_param'] == 5
    assert session.parameters._params['a_param'].func is my_param