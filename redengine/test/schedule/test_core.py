
import datetime
import logging
import time
import os, re
import multiprocessing

import pytest
import pandas as pd
from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo

from redengine.log.log_record import LogRecord, TaskLogRecord
import redengine
from redengine import Session
from redengine.core import Scheduler, Parameters
from redengine.log.log_record import MinimalRecord
from redengine.tasks import FuncTask
from redengine.test.task.func.test_run import run_inaction
from redengine.time import TimeDelta
from redengine.exc import TaskInactionException
from redengine.conditions import SchedulerCycles, SchedulerStarted, TaskStarted, AlwaysFalse, AlwaysTrue
from redengine.args import Private

def run_failing():
    raise RuntimeError("Task failed")

def run_succeeding():
    pass

def run_inacting():
    raise TaskInactionException()

def create_line_to_file():
    with open("work.txt", "a") as file:
        file.write("line created\n")

def run_with_param(int_5):
    assert int_5 == 5

def run_creating_child():

    proc = multiprocessing.Process(target=run_succeeding, daemon=True)
    proc.start()


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_execution(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:
        # To be confident the scheduler won't lie to us
        # we test the task execution with a job that has
        # actual measurable impact outside redengine
        FuncTask(create_line_to_file, name="add line to file", start_cond=AlwaysTrue(), execution=execution),

        session.config.shut_cond = (TaskStarted(task="add line to file") >= 3) | ~SchedulerStarted(period=TimeDelta("5 second"))

        session.start()
        # Sometimes in CI the task may end up to be started only twice thus we tolerate slightly
        with open("work.txt", "r") as file:
            assert 2 <= len(list(file))

@pytest.mark.parametrize("get_handler", [
    pytest.param(lambda: RepoHandler(repo=MemoryRepo(model=TaskLogRecord)), id="Memory with model"),
    pytest.param(lambda: RepoHandler(repo=MemoryRepo()), id="Memory with dict"),
])
@pytest.mark.parametrize("execution", ["main", "thread", "process"])
@pytest.mark.parametrize(
    "task_func,run_count,fail_count,success_count,inact_count",
    [
        pytest.param(
            run_succeeding, 
            3, 0, 3, 0,
            id="Succeeding task"),

        pytest.param(
            run_failing, 
            3, 3, 0, 0,
            id="Failing task"),
        pytest.param(
            run_inacting, 
            3, 0, 0, 3,
            id="Inacting task"),
    ],
)
def test_task_log(tmpdir, execution, task_func, run_count, fail_count, success_count, inact_count, get_handler):
    """Test the task logging thoroughly including the common
    logging schemes, execution (main, thread, process) and 
    outcomes (fail, success, inaction).

    This task may take some time but should cover most of the
    issues with logging.
    """

    with tmpdir.as_cwd() as old_dir:
        # Set session (and logging)
        session = Session(config={"debug": True, "silence_task_prerun": False})
        redengine.session = session
        session.set_as_default()

        task_logger = logging.getLogger(session.config.task_logger_basename)
        task_logger.handlers = [
            get_handler()
        ]

        task = FuncTask(task_func, name="mytask", start_cond=AlwaysTrue(), execution=execution)

        session.config.shut_cond = (TaskStarted(task="mytask") >= run_count) | ~SchedulerStarted(period=TimeDelta("10 second"))
        session.start()

        assert bool(TaskStarted(task="mytask") >= run_count)

        # Test history
        history = list(task.logger.get_records())
        logger = task.logger
        assert run_count == logger.filter_by(action="run").count()
        assert success_count == logger.filter_by(action="success").count()
        assert fail_count == logger.filter_by(action="fail").count()
        assert inact_count == logger.filter_by(action="inaction").count()

        # Test relevant log items
        for record in history:
            if not isinstance(record, dict):
                record = record.dict()
            assert record["task_name"] == "mytask"
            assert isinstance(record["created"], float)
            assert isinstance(record["start"], datetime.datetime)
            if record["action"] != "run":
                assert isinstance(record["end"], datetime.datetime)
                assert isinstance(record["runtime"], datetime.timedelta)

            # Test traceback
            if record["action"] == "fail":
                assert re.match(
                    r'Traceback \(most recent call last\):\n  File ".+", line [0-9]+, in [\s\S]+, in run_failing\n    raise RuntimeError\("Task failed"\)\nRuntimeError: Task failed', 
                    record["exc_text"]
                )

        # Test some other relevant APIs
        assert history == list(task.logger.get_records())
        assert history[-1] == task.logger.get_latest()
        assert history == list(session.get_task_log())

        assert run_count == len(list(task.logger.get_records(action="run")))
        assert success_count == len(list(task.logger.get_records(action="success")))
        assert fail_count == len(list(task.logger.get_records(action="fail")))
        assert inact_count == len(list(task.logger.get_records(action="inaction")))

@pytest.mark.parametrize("mode", ["use logs", "use cache"])
@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_status(session, execution, mode):
    session.config.force_status_from_logs = True if mode == "use logs" else False

    task_success = FuncTask(
        run_succeeding, 
        start_cond="every 20 seconds", 
        name="task success",
        execution=execution
    )
    task_fail = FuncTask(
        run_failing, 
        start_cond="every 20 seconds", 
        name="task fail",
        execution=execution
    )
    task_inact = FuncTask(
        run_inaction, 
        start_cond="every 20 seconds", 
        name="task inact",
        execution=execution
    )
    task_not_run = FuncTask(
        run_inaction, 
        start_cond=AlwaysFalse(), 
        name="task not run",
        execution=execution
    )
    session.config.shut_cond = SchedulerCycles() >= 5
    session.start()
    assert task_success.last_run is not None
    assert task_success.last_success is not None
    assert task_success.last_fail is None

    assert task_fail.last_run is not None
    assert task_fail.last_fail is not None
    assert task_fail.last_success is None

    assert task_inact.last_run is not None

    assert task_not_run.last_run is None
    assert task_not_run.last_success is None
    assert task_not_run.last_fail is None

    assert task_success.status == "success"
    assert task_fail.status == "fail"
    assert task_inact.status == "inaction"
    assert task_not_run.status == None


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_force_run(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:
        task = FuncTask(
            run_succeeding, 
            start_cond=AlwaysFalse(), 
            name="task",
            execution=execution
        )
        task.force_run = True

        session.config.shut_cond = SchedulerCycles() >= 5
        session.start()

        logger = task.logger
        assert 1 == logger.filter_by(action="run").count()

        # The force_run should have reseted as it should have run once
        assert not task.force_run


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_disabled(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            run_succeeding, 
            start_cond=AlwaysFalse(), 
            name="task",
            execution=execution
        )
        task.disabled = True

        session.config.shut_cond = SchedulerCycles() >= 5
        session.start()

        history = task.logger.get_records()
        assert 0 == sum([record for record in history if record["action"] == "run"])

        assert task.disabled


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_force_disabled(tmpdir, execution, session):
    # NOTE: force_run overrides disabled
    # as it is more practical to keep 
    # a task disabled and force it running
    # manually than prevent force run with
    # disabling
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            run_succeeding, 
            start_cond=AlwaysFalse(), 
            name="task",
            execution=execution
        )
        task.disabled = True
        task.force_run = True

        session.config.shut_cond = SchedulerCycles() >= 5
        session.start()

        logger = task.logger
        assert 1 == logger.filter_by(action="run").count()
        assert 1 == logger.filter_by(action="success").count()

        assert task.disabled
        assert not task.force_run # This should be reseted

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_priority(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:

        task_1 = FuncTask(run_succeeding, name="1", priority=100, start_cond=AlwaysTrue(), execution=execution)
        task_3 = FuncTask(run_failing, name="3", priority=10, start_cond=AlwaysTrue(), execution=execution)
        task_2 = FuncTask(run_failing, name="2", priority=50, start_cond=AlwaysTrue(), execution=execution)
        task_4 = FuncTask(run_failing, name="4", start_cond=AlwaysTrue(), execution=execution)

        assert 0 == task_4.priority

        session.config.shut_cond = (SchedulerCycles() == 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))

        session.start()
        assert session.scheduler.n_cycles == 1 

        task_1_start = list(task_1.logger.get_records())[0].created
        task_2_start = list(task_2.logger.get_records())[0].created
        task_3_start = list(task_3.logger.get_records())[0].created
        task_4_start = list(task_4.logger.get_records())[0].created
        
        assert task_1_start < task_2_start < task_3_start < task_4_start

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_pass_params_as_global(tmpdir, execution, session):
    # thread-Parameters has been observed to fail rarely
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(run_with_param, name="parametrized", start_cond=AlwaysTrue(), execution=execution)

        session.config.shut_cond = (TaskStarted(task="parametrized") >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))

        # Passing global parameters
        session.parameters["int_5"] = 5
        session.parameters["extra_param"] = "something"

        session.scheduler()

        logger = task.logger
        assert 1 == logger.filter_by(action="run").count()
        assert 1 == logger.filter_by(action="success").count()
        assert 0 == logger.filter_by(action="fail").count()

@pytest.mark.parametrize("parameters", [
    pytest.param({"int_5": 5}, id="dict"), 
    pytest.param(Parameters(int_5=5), id="Parameters"),
    pytest.param(Parameters(int_5=Private(5)), id="Parameter with secret"),
])
@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_pass_params_as_local(tmpdir, execution, parameters, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            run_with_param, 
            name="parametrized", 
            parameters=parameters,
            start_cond=AlwaysTrue(),
            execution=execution
        )
        session.config.shut_cond = (TaskStarted(task="parametrized") >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))

        session.start()

        logger = task.logger
        assert 1 == logger.filter_by(action="run").count()
        assert 1 == logger.filter_by(action="success").count()
        assert 0 == logger.filter_by(action="fail").count()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_pass_params_as_local_and_global(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            run_with_param, 
            name="parametrized", 
            parameters={"int_5": 5},
            start_cond=AlwaysTrue(),
            execution=execution
        )

        session.config.shut_cond = (TaskStarted(task="parametrized") >= 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))

        # Additional parameters
        session.parameters["extra_param"] = "something"

        session.start()

        logger = task.logger
        assert 1 == logger.filter_by(action="run").count()
        assert 1 == logger.filter_by(action="success").count()
        assert 0 == logger.filter_by(action="fail").count()


# Only needed for testing start up and shutdown
def create_line_to_startup_file():
    with open("start.txt", "w") as file:
        file.write("line created\n")

def create_line_to_shutdown():
    with open("shut.txt", "w") as file:
        file.write("line created\n")

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_startup_shutdown(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:
        
        FuncTask(create_line_to_startup_file, name="startup", on_startup=True, execution=execution)
        FuncTask(create_line_to_shutdown, name="shutdown", on_shutdown=True, execution=execution)

        session.config.shut_cond = AlwaysTrue()

        session.start()
        if execution == "thread":
            # It may take a moment for the
            # thread to write to the file
            timeout = 5
            time_taken = 0
            while os.path.exists("shut.txt"):
                time.sleep(0.01)
                time_taken += 0.01
                if time_taken > timeout:
                    break
        
        assert os.path.exists("start.txt")
        assert os.path.exists("shut.txt")

        assert list(session.get_task_log()) != []

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_logging_repo(tmpdir, execution):
    from redbird.logging import RepoHandler
    from redbird.repos import MemoryRepo
    session = Session()
    session.set_as_default()

    handler = RepoHandler(repo=MemoryRepo(model=MinimalRecord))

    logger = logging.getLogger("redengine.task")
    logger.handlers = []
    logger.addHandler(handler)


    with tmpdir.as_cwd() as old_dir:

        task_1 = FuncTask(run_succeeding, name="1", priority=100, start_cond=AlwaysTrue(), execution=execution)
        task_3 = FuncTask(run_failing, name="3", priority=10, start_cond=AlwaysTrue(), execution=execution)
        task_2 = FuncTask(run_failing, name="2", priority=50, start_cond=AlwaysTrue(), execution=execution)
        task_4 = FuncTask(run_failing, name="4", start_cond=AlwaysTrue(), execution=execution)

        assert 0 == task_4.priority

        session.config.shut_cond = (SchedulerCycles() == 1) | ~SchedulerStarted(period=TimeDelta("2 seconds"))
        session.start()
        assert session.scheduler.n_cycles == 1 

        task_1_start = list(task_1.logger.get_records())[0].created
        task_2_start = list(task_2.logger.get_records())[0].created
        task_3_start = list(task_3.logger.get_records())[0].created
        task_4_start = list(task_4.logger.get_records())[0].created
        
        assert task_1_start < task_2_start < task_3_start < task_4_start
