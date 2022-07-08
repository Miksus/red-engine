import datetime
import logging
import pytest
import multiprocessing
from queue import Empty

import pandas as pd
from redbird.logging import RepoHandler

from redengine import Session
from redengine.log.log_record import MinimalRecord

from redengine.tasks import FuncTask

def run_success():
    pass

def test_running(tmpdir, session):
    
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main"
        )
        task.log_running()
        assert "run" == task.status
        assert task.is_running

def test_success(tmpdir, session):
    
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main"
        )
        task.log_running()
        task.log_success()
        assert "success" == task.status
        assert not task.is_running

def test_fail(tmpdir, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main"
        )
        task.log_running()
        task.log_failure()
        assert "fail" == task.status
        assert not task.is_running

def test_without_running(tmpdir, session):
    "An edge case if for mysterious reason the task did not log running. Logging should still not crash"
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main"
        )
        task.log_failure()
        assert "fail" == task.status
        assert not task.is_running

def test_handle(tmpdir, session):

    def create_record(action, task_name):
        # Util func to create a LogRecord
        record = logging.LogRecord(
            level=logging.INFO,
            exc_info=None,
            # These should not matter:
            name="redengine.task._process",
            pathname=__file__,
            lineno=1,
            msg="",
            args=None,
        )
        record.action = action
        record.task_name = task_name
        return record

    # Tests Task.handle (used in process tasks)
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main",
            name="a task"
        )
        # Creating the run log
        record_run = create_record("run", task_name="a task")

        # Creating the outcome log
        record_finish = create_record("success", task_name="a task")
        
        task.log_record(record_run)
        assert "run" == task.status
        assert task.is_running

        task.log_record(record_finish)
        assert "success" == task.status
        assert not task.is_running

        records = session.get_task_log()
        records = [
            record.dict(exclude={"created"})
            for record in records
        ]
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_without_handlers(tmpdir, session):
    session.config.force_status_from_logs = True
    session.config.task_logger_basename = 'hdlr_test.task'

    logger = logging.getLogger("hdlr_test.task")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with pytest.warns(UserWarning) as warns:
        task = FuncTask(
            lambda : None, 
            name="task 1",
            start_cond="always true",
            #logger="redengine.task.test",
            execution="main",
        )
    
    # Test warnings
    
    #assert str(warns[0].message) == "Logger 'redengine.task.test' for task 'task 1' does not have ability to be read. Past history of the task cannot be utilized."
    warn_messages = [str(w.message) for w in warns]
    assert warn_messages == [
        "Logger hdlr_test.task cannot be read. Logging is set to memory. To supress this warning, please set a handler that can be read (redbird.logging.RepoHandler)"
    ]

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], RepoHandler)

def test_without_handlers_status_warnings(tmpdir, session):
    session.config.force_status_from_logs = True

    logger = logging.getLogger("redengine.task")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with pytest.warns(UserWarning) as warns:
        task = FuncTask(
            lambda : None, 
            name="task 1",
            start_cond="always true",
            logger_name="redengine.task.test",
            execution="main",
        )
    # Removing the handlers that were added
    
    # Test warnings
    expected_warnings = [
        'Logger redengine.task cannot be read. Logging is set to memory. To supress this warning, please set a handler that can be read (redbird.logging.RepoHandler)'
        #"Logger 'redengine.task.test' for task 'task 1' does not have ability to be read. Past history of the task cannot be utilized.",
        #"Task 'task 1' logger is not readable. Latest run unknown.",
        #"Task 'task 1' logger is not readable. Latest success unknown.",
        #"Task 'task 1' logger is not readable. Latest fail unknown.",
        #"Task 'task 1' logger is not readable. Latest terminate unknown.",
        #"Task 'task 1' logger is not readable. Latest inaction unknown."
    ]
    actual_warnings = [str(warn.message) for warn in warns]
    assert expected_warnings == actual_warnings

    # Removing the handlers that were added
    # to test without handlers
    logger.handlers = []

    task()
    # Cannot know the task.status as there is no log about it
    assert task.status == 'success'
    with pytest.warns(UserWarning) as warns:
        assert task.get_status() is None
    
    assert list(str(w.message) for w in warns) == [
        "Logger 'redengine.task.test' for task 'task 1' does not have ability to be read. Past history of the task cannot be utilized.",
        "Task 'task 1' logger is not readable. Status unknown."
    ]

    session.config.force_status_from_logs = False
    with pytest.warns(UserWarning) as warns:
        task = FuncTask(
            lambda : None, 
            name="task 2",
            start_cond="always true",
            logger="redengine.task.test",
            execution="main",
        )
    assert list(str(w.message) for w in warns) == [
        'Logger redengine.task cannot be read. Logging is set to memory. To supress this warning, please set a handler that can be read (redbird.logging.RepoHandler)'
    ]

    task()
    # Can know the task.status as stored in a variable
    assert task.status == "success"
    assert task.get_status() == "success"

@pytest.mark.parametrize("method",
    [
        pytest.param("log_success", id="Success"),
        pytest.param("log_failure", id="Failure"),
        pytest.param("log_inaction", id="Inaction"),
        pytest.param("log_termination", id="Termination"),
    ],
)
def test_action_start(tmpdir, method, session):
    
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None,
            execution="main",
        )
        task.log_running()
        getattr(task, method)()

        records = list(map(lambda e: e.dict(), session.get_task_log()))
        assert len(records) == 2

        # First should not have "end"
        first = records[0]
        assert first['created'] >= datetime.datetime(2000, 1, 1).timestamp()

        # Second should and that should be datetime
        last = records[1]
        assert first['created'] <= last['created']
        assert last['created'] < datetime.datetime(2200, 1, 1).timestamp()

def test_process_no_double_logging(tmpdir, session):
    # 2021-02-27 there is a bug that Raspbian logs process task logs twice
    # while this is not occuring on Windows. This tests the bug.
    #!NOTE: This test requires there are two handlers in 
    # redengine.task logger (Memory and Stream in this order)

    expected_actions = ["run", "success"]
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            run_success, 
            name="a task",
            execution="process"
        )

        log_queue = multiprocessing.Queue(-1)

        # Start the process
        proc = multiprocessing.Process(target=task._run_as_process, args=(None, None, log_queue, session.config, []), daemon=None) 
        proc.start()

        # Do the logging manually (copied from the method)
        actual_actions = []
        records = []
        while True:
            try:
                record = log_queue.get(block=True, timeout=3)
            except Empty:
                break
            else:
                records.append(record)
                # task.log_record(record)
                actual_actions.append(record.action)

        # If fails here, double logging caused by creating too many records
        # Obseved to fail rarely with py36 (c2f0368ffa56c5b8933f1afa2917f2be1555fb7a)
        assert len(records) >= 2 # Testing not too few records (else not double logging bug)
        assert (
            ["run", "success"] == [rec.action for rec in records]
        ), "Double logging. Caused by creating multiple records (Task.log_running & Task.log_success) to the queue."

        # Testing there is no log records yet in the log
        # (as the records should not been handled yet)
        df = pd.DataFrame(session.get_task_log())
        assert df.empty, "Double logging. The log file is not empty before handling the records. Process bypasses the queue."
        
        for record in records:
            task.log_record(record)

        # If fails here, double logging caused by multiple handlers
        handlers = task.logger.logger.handlers
        handlers[0] # Checking it has atleast 2
        handlers[1] # Checking it has atleast 2
        assert (
            isinstance(handlers[1], logging.StreamHandler)
            and isinstance(handlers[0], RepoHandler)
            and len(handlers) == 2
        ), f"Double logging. Too many handlers: {handlers}"

        # If fails here, double logging caused by Task.log_record
        n_run = len(list(session.get_task_log(task_name="a task", action="run")))
        n_success = len(list(session.get_task_log(task_name="a task", action="success")))

        assert n_run > 0 and n_success > 0, "No log records formed to log."

        assert n_run == 1 and n_success == 1, "Double logging. Bug in Task.log_record probably."