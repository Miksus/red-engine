
import pytest

from redengine.args import Private, Return
from redengine import Scheduler
from redengine.core import parameters
from redengine.tasks import FuncTask
from redengine.conditions import TaskStarted
from redengine.args import FuncArg


def func_with_arg(value):
    pass

def func_x_with_return():
    return "x"

def func_x_with_arg(myparam):
    assert myparam == "x"


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_normal(session, execution):

    task_return = FuncTask(
        func_x_with_return, 
        name="return task",
        start_cond="~has started",
        execution=execution,
        force_run=True
    )
    task = FuncTask(
        func_x_with_arg, 
        name="a task",
        start_cond="after task 'return task'",
        parameters={"myparam": Return('return task')},
        execution=execution
    )

    assert task.status is None

    session.config.shut_cond = TaskStarted(task="a task") >= 1
    session.start()

    assert dict(session.returns) == {task_return: "x", task: None}
    assert "success" == task_return.status
    assert "success" == task.status

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_missing(session, execution):
    session.config.silence_task_prerun = True # Default in prod
    
    task = FuncTask(
        func_with_arg, 
        parameters={"myparam": Return('return task')},
        name="a task",  
        force_run=True,
        execution=execution
    )
 
    assert task.status is None
    session.config.shut_cond = TaskStarted(task="a task") >= 1
    session.start()

    assert "fail" == task.status

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_default(session, execution):
    task = FuncTask(
        func_with_arg, 
        name="return task", 
    )
    task = FuncTask(
        func_x_with_arg, 
        parameters={"myparam": Return('return task', default="x")},
        name="a task", 
        execution=execution, 
        force_run=True,
    )

    assert task.status is None
    session.config.shut_cond = TaskStarted(task="a task") >= 1
    session.start()

    assert "success" == task.status