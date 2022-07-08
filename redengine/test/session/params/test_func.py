
import pytest

from redengine.args import Private, Return
from redengine import Scheduler
from redengine.conditions.scheduler import SchedulerCycles
from redengine.core import parameters
from redengine.tasks import FuncTask
from redengine.conditions import TaskStarted, AlwaysTrue
from redengine.args import FuncArg, Arg


def get_x():
    return "x"

def func_x_with_arg(myparam):
    assert myparam == "x"

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_simple(session, execution):

    task = FuncTask(
        func_x_with_arg, 
        parameters={"myparam": FuncArg(get_x)}, 
        execution=execution, 
        name="a task", 
        start_cond=AlwaysTrue()
    )
    session.config.shut_cond = (TaskStarted(task="a task") >= 1)

    assert task.status is None
    session.start()

    assert "success" == task.status

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_session(session, execution):

    session.parameters["myparam"] = FuncArg(get_x)

    task = FuncTask(
        func_x_with_arg, 
        execution=execution, 
        name="a task", 
        start_cond=AlwaysTrue()
    )
    session.config.shut_cond = (TaskStarted(task="a task") >= 1)

    assert task.status is None
    session.start()

    assert "success" == task.status

class UnPicklable:
    def __getstate__(self):
        raise RuntimeError("Cannot be pickled")

def get_unpicklable():
    return UnPicklable()

def func_check_unpicklable(myparam):
    assert isinstance(myparam, UnPicklable)

@pytest.mark.parametrize("execution", ["process"])
def test_unpicklable(session, execution):
    "Test a FuncArg that returns unpicklable item"
    task = FuncTask(
        func_check_unpicklable, 
        parameters={"myparam": FuncArg(get_unpicklable)}, 
        execution=execution, 
        name="a task", 
        start_cond=AlwaysTrue()
    )

    session.config.shut_cond = (TaskStarted(task="a task") >= 1) 

    assert task.status is None
    session.start()
    assert "success" == task.status