
import pytest

from redengine.conditions import (
    TaskFinished, 
    TaskFailed, 
    TaskSucceeded,

    DependFinish,
    DependFailure,
    DependSuccess,
    TaskStarted,
    TaskTerminated,
)
from redengine.core.task import Task
from redengine.tasks import FuncTask



def run_task(fail=False):
    print("Running func")
    if fail:
        raise RuntimeError("Task failed")

@pytest.mark.parametrize('execution_number', range(10))
def test_task_status_race(tmpdir, session, execution_number):

    # c = logging.LogRecord("",1, "a", "a", "2", (), "").created
    # c = time.time()
    # t = time.time()
    # c = datetime.datetime.fromtimestamp(c)
    # t = datetime.datetime.now()
    # assert t >= c
    # return

    condition = TaskFinished(task="runned task")
    task = FuncTask(
        run_task, 
        name="runned task",
        execution="main"
    )
    task(params={"fail": False})

    # Imitating the __bool__
    assert condition.observe(task=task)

@pytest.mark.parametrize(
    "cls,succeeding,expected",
    [
        pytest.param(
            TaskFinished, True, 
            True,
            id="TaskFinished Success"),
        pytest.param(
            TaskFinished, False, 
            True,
            id="TaskFinished Failure"),

        pytest.param(
            TaskSucceeded, True, 
            True,
            id="TaskSucceeded Success"),
        pytest.param(
            TaskSucceeded, False, 
            False,
            id="TaskSucceeded Failure"),

        pytest.param(
            TaskFailed, True, 
            False,
            id="TaskFailed Success"),
        pytest.param(
            TaskFailed, False, 
            True,
            id="TaskFailed Failure"),
    ],
)
def test_task_status(tmpdir, session, cls, succeeding, expected):
    # RACE CONDITION 2021-08-16: 'TaskFailed Failure' failed due to assert bool(condition) if expected else not bool(condition)

    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task")

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # Has not yet ran
        assert not bool(condition)

        # Now has
        try:
            task(params={"fail": not succeeding})
        except: 
            pass

        # we sleep 20ms to 
        # There is a very small inaccuracy in time.time() that is used by
        # logging library to create LogRecord.created. On Windows this 
        # inaccuracy can be 16ms (https://stackoverflow.com/questions/1938048/high-precision-clock-in-python)
        # and in some cases the task is not registered to have run as 
        # in memory logging is way too fast. Therefore we just wait
        # 20ms to fix the issue
        # time.sleep(0.02) 
        assert bool(condition) if expected else not bool(condition)


@pytest.mark.parametrize(
    "cls,expected",
    [
        pytest.param(
            DependFinish, 
            True,
            id="DependFinish"),

        pytest.param(
            DependSuccess, 
            False,
            id="DependSuccess"),

        pytest.param(
            DependFailure, 
            True,
            id="DependFailure"),
    ],
)
def test_task_depend_fail(tmpdir, session, cls, expected):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task", depend_task="prerequisite task")

        depend_task = FuncTask(
            run_task, 
            name="prerequisite task",
            execution="main"
        )

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # ------------------------ t0
        assert not bool(condition)


        # depend_task
        # -----|------------------- t0
        try: depend_task(params={"fail": True})
        except: pass
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task
        # -----|-----------|------- t0
        task()
        assert not bool(condition)


        # depend_task     task     depend_task
        # -----|-----------|-----------|----------- t0
        try: depend_task(params={"fail": True})
        except: pass
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task     depend_task     task
        # -----|-----------|-----------|------------|-------- t0
        task()
        assert not bool(condition)


@pytest.mark.parametrize(
    "cls,expected",
    [
        pytest.param(
            DependFinish, 
            True,
            id="DependFinish"),

        pytest.param(
            DependSuccess, 
            True,
            id="DependSuccess"),

        pytest.param(
            DependFailure, 
            False,
            id="DependFailure"),
    ],
)
def test_task_depend_success(tmpdir, session, cls, expected):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        condition = cls(task="runned task", depend_task="prerequisite task")

        depend_task = FuncTask(
            run_task, 
            name="prerequisite task",
            execution="main"
        )

        task = FuncTask(
            run_task, 
            name="runned task",
            execution="main"
        )

        # ------------------------ t0
        assert not bool(condition)


        # depend_task
        # -----|------------------- t0
        depend_task(params={"fail": False})
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task
        # -----|-----------|------- t0
        task()
        assert not bool(condition)


        # depend_task     task     depend_task
        # -----|-----------|-----------|----------- t0
        depend_task(params={"fail": False})
        assert bool(condition) if expected else not bool(condition)


        # depend_task     task     depend_task     task
        # -----|-----------|-----------|------------|-------- t0
        task()
        assert not bool(condition)


@pytest.mark.parametrize(
    "cls,string",
    [
        pytest.param(TaskFinished, "task 'mytask' finished", id="TaskFinished"), 
        pytest.param(TaskFailed, "task 'mytask' failed", id="TaskFailed"), 
        pytest.param(TaskSucceeded, "task 'mytask' succeeded", id="TaskSucceeded"),
        pytest.param(TaskStarted, "task 'mytask' started", id="TaskStarted"),
        pytest.param(TaskTerminated, "task 'mytask' terminated", id="TaskStarted"),

        pytest.param(DependFinish, "task 'mydep' finished before 'mytask' started", id="DependFinish"),
        pytest.param(DependFailure, "task 'mydep' failed before 'mytask' started", id="DependFailure"),
        pytest.param(DependSuccess, "task 'mydep' succeeded before 'mytask' started", id="DependSuccess"),
    ],
)
def test_display(cls, string):
    task = FuncTask(func=lambda: None, name="mytask")
    depend_task = FuncTask(func=lambda: None, name="mydep")
    s = str(cls(task=task, depend_task=depend_task))
    assert s == string