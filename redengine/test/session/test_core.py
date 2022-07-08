
import logging
from redengine.core.log.adapter import TaskAdapter
from redengine.tasks import FuncTask
from redengine.core import Parameters, Scheduler

def test_get_task(session):

    task = FuncTask(
        lambda : None, 
        name="example",
        execution="main"
    )
    
    # By string
    t = session.get_task(task.name)
    assert t is task

    # By task (returns itself)
    t = session.get_task(task)
    assert t is task


def test_tasks_attr(session):

    task1 = FuncTask(
        lambda : None, 
        name="example 1",
        execution="main"
    )
    task2 = FuncTask(
        lambda : None, 
        name="example 2",
        execution="main"
    )
        
    assert session.tasks == {task1, task2}

def test_clear(session):

    assert session.tasks == set()
    assert Parameters() == session.parameters
    # assert session.scheduler is None

    task1 = FuncTask(
        lambda : None, 
        name="example 1",
        execution="main"
    )
    task2 = FuncTask(
        lambda : None, 
        name="example 2",
        execution="main"
    )
    session.parameters["x"] = 1
    
    assert Parameters(x=1) == session.parameters
    assert session.tasks == {task1, task2}

    session.clear()

    assert session.tasks == set()
    assert Parameters() == session.parameters

def test_get_repo(session):

    logger = logging.getLogger("redengine.task")
    assert session.get_repo() is logger.handlers[0].repo

    # Test the one used in the task logging is also the same
    assert session.get_repo() is TaskAdapter(logger, task=None)._get_repo()