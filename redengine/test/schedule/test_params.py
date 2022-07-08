
import pytest
import redengine
from redengine.conditions import DependSuccess


from redengine.tasks import FuncTask
from redengine.time import TimeDelta
from redengine.conditions import SchedulerCycles, SchedulerStarted, TaskStarted, AlwaysFalse, AlwaysTrue

from redengine.args import Arg, Return, Session, Task, FuncArg #, Param, Session

# Example functions
# -----------------
def get_some_value():
    return 'some func value'

def get_some_value_with_arg(pass_yes):
    assert pass_yes == 'yes'
    return 'some func value 2'

# Example task functions
# ----------------------

def run_with_output():
    return 'some value' 

def run_with_func_arg(arg=FuncArg(get_some_value), arg2=FuncArg(get_some_value_with_arg, pass_yes='yes')):
    assert arg == 'some func value'
    assert arg2 == 'some func value 2'

def run_with_session_arg(arg=Arg('my_arg')):
    assert arg == 'some session value' 

def run_with_return(arg=Return('task_with_output')):
    assert arg == 'some value'

def run_with_task(arg = Task(), arg2 = Task('another_task')):
    # arg should be the task itself, arg2 another task
    assert isinstance(arg, redengine.core.Task)
    assert isinstance(arg2, redengine.core.Task)
    assert arg.name == 'my_task'
    assert arg2.name == 'another_task'

def run_with_session(arg=Session()):
    assert isinstance(arg, redengine.Session)
    assert arg.parameters['my_arg'] == 'some session value'

# Tests
# -----

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_func_arg(execution, session):
    task = FuncTask(func=run_with_func_arg, start_cond=AlwaysTrue(), execution=execution, session=session)

    session.config.shut_cond = (SchedulerCycles() >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))
    session.start()

    logger = task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_session_arg(execution, session):
    task = FuncTask(func=run_with_session_arg, start_cond=AlwaysTrue(), execution=execution, session=session)

    session.config.shut_cond = (SchedulerCycles() >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))
    session.parameters['my_arg'] = 'some session value'
    session.start()

    logger = task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_return(execution, session):

    input_task = FuncTask(func=run_with_output, name="task_with_output", start_cond=AlwaysTrue(), execution=execution, session=session)
    task = FuncTask(func=run_with_return, name="task_use_output", start_cond=DependSuccess(depend_task=input_task), execution=execution, session=session)

    session.config.shut_cond = (TaskStarted(task="task_use_output") >= 1) | ~SchedulerStarted(period=TimeDelta("10 seconds"))
    session.start()

    logger = task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()

    logger = input_task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()

    assert session.returns[input_task] == 'some value'

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_session_as_arg(execution, session):
    task = FuncTask(func=run_with_session, start_cond=AlwaysTrue(), execution=execution, session=session)

    session.config.shut_cond = (SchedulerCycles() >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))
    session.parameters['my_arg'] = 'some session value'
    session.start()

    logger = task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_as_arg(execution, session):
    another_task = FuncTask(func=run_with_output, name="another_task", session=session)
    task = FuncTask(func=run_with_task, name="my_task", start_cond=AlwaysTrue(), execution=execution, session=session)

    session.config.shut_cond = (SchedulerCycles() >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))
    session.start()

    logger = task.logger
    assert 1 == logger.filter_by(action="run").count()
    assert 1 == logger.filter_by(action="success").count()
    assert 0 == logger.filter_by(action="fail").count()