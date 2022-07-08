from redengine.tasks import FuncTask
from redengine.core import Parameters, Scheduler

def test_run(tmpdir, session):
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
    session.run("example 2")
    assert task1.status is None
    assert task2.status == "success"

def test_run_obey_cond(tmpdir, session):
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
    session.run("example 2", obey_cond=True)
    assert task1.status is None
    assert task2.status is None # start cond is false