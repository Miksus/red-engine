
from functools import partial
from textwrap import dedent

import pytest
from redengine.conditions.task.task import DependSuccess
from redengine.core import Task, Scheduler

from redengine.tasks import FuncTask
from redengine.conditions import SchedulerCycles, true

def do_success(**kwargs):
    ...

def do_fail(**kwargs):
    raise RuntimeError("Deliberate fail")

def test_task_init(session):
    timeline = []

    @session.hook_task_init()
    def myhook(task):
        timeline.append("Function hook called")
        assert isinstance(task, DummyTask)
        assert not hasattr(task, "name") # Should not yet have created this attr
    
    @session.hook_task_init()
    def mygenerhook(task):
        timeline.append("Generator hook called (pre)")
        assert isinstance(task, DummyTask)
        assert not hasattr(task, "name") # Should not yet have created this attr
        yield 
        assert hasattr(task, "session") # Should now have it
        timeline.append("Generator hook called (post)")

    class DummyTask(Task):

        def execute(self, *args, **kwargs):
            return 


    assert session.hooks.task_init == [myhook, mygenerhook] # The func is in different namespace thus different

    timeline.append("Main")
    mytask = DummyTask(name="dummy")
    assert timeline == [
        "Main",
        "Function hook called",
        "Generator hook called (pre)",
        "Generator hook called (post)",
    ]


def test_scheduler_startup(session):
    timeline = []

    @session.hook_startup()
    def my_startup_hook(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (startup)")

    @session.hook_scheduler_cycle()
    def my_cycle_hook(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (cycle)")

    @session.hook_shutdown()
    def my_shutdown_hook(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (shutdown)")


    @session.hook_startup()
    def my_startup_hook_generator(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (startup, generator first)")
        yield
        timeline.append("ran hook (startup, generator second)")

    @session.hook_scheduler_cycle()
    def my_cycle_hook_generator(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (cycle, generator first)")
        yield
        timeline.append("ran hook (cycle, generator second)")

    @session.hook_shutdown()
    def my_shutdown_hook_generator(sched):
        assert isinstance(sched, Scheduler)
        timeline.append("ran hook (shutdown, generator first)")
        yield
        timeline.append("ran hook (shutdown, generator second)")
    

    FuncTask(lambda: timeline.append("ran TASK (startup)"), name="start", on_startup=True, execution="main")
    task1 = FuncTask(lambda: timeline.append("ran TASK (normal 1)"), name="1", execution="main", start_cond=true, priority=1)
    task2 = FuncTask(lambda: timeline.append("ran TASK (normal 2)"), name="2", execution="main", start_cond=DependSuccess(depend_task=task1), priority=0)
    FuncTask(lambda: timeline.append("ran TASK (shutdown)"), name="shut", on_shutdown=True, execution="main")

    session.config.shut_cond = SchedulerCycles(_eq_=2)
    session.start()
    
    assert session.hooks.scheduler_startup == [my_startup_hook, my_startup_hook_generator]
    assert session.hooks.scheduler_cycle == [my_cycle_hook, my_cycle_hook_generator]
    assert session.hooks.scheduler_shutdown == [my_shutdown_hook, my_shutdown_hook_generator]

    assert timeline == [
        "ran hook (startup)", 
        "ran hook (startup, generator first)", 
        "ran TASK (startup)", 
        "ran hook (startup, generator second)", 

        "ran hook (cycle)", 
        "ran hook (cycle, generator first)", 
        "ran TASK (normal 1)",
        "ran TASK (normal 2)",
        "ran hook (cycle, generator second)", 

        "ran hook (cycle)", 
        "ran hook (cycle, generator first)", 
        "ran TASK (normal 1)",
        "ran TASK (normal 2)",
        "ran hook (cycle, generator second)", 

        "ran hook (shutdown)", 
        "ran hook (shutdown, generator first)", 
        "ran TASK (shutdown)", 
        "ran hook (shutdown, generator second)", 
    ]

# Hooks
def myhook_normal(task, file):
    assert isinstance(task, Task)
    with open(file, "a") as f:
        f.write("Function hook called\n")

def myhook_gener(task, file):
    assert isinstance(task, Task)
    with open(file, "a") as f:
        f.write("Generator hook inited\n")
    exc_type, exc, tb = yield
    with open(file, "a") as f:
        f.write(f"Generator hook continued with {exc_type} {exc}\n")


@pytest.mark.parametrize("func,exc_type,exc", [pytest.param(do_success, None, None, id="success"), pytest.param(do_fail, RuntimeError, RuntimeError('Deliberate fail'), id="fail")])
@pytest.mark.parametrize("execution", ['main', 'thread', 'process'])
def test_task_execute(session, execution, tmpdir, func, exc_type, exc):

    file = tmpdir.join("timeline.txt")

    session.hook_task_execute()(partial(myhook_normal, file=file))
    session.hook_task_execute()(partial(myhook_gener, file=file))

    with open(file, "w") as f:
        f.write("\nStarting\n")

    task = FuncTask(func, execution=execution, parameters={"testfile": str(file)}, start_cond="true", name="mytask")
    session.config.shut_cond = SchedulerCycles(_ge_=1)
    session.start()
    with open(file) as f:
        cont = f.read()
    assert dedent(f"""
    Starting
    Function hook called
    Generator hook inited
    Generator hook continued with {exc_type} {exc}
    """) == cont