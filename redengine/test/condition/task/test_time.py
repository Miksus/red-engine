
import logging
from typing import List, Tuple

import pytest
import pandas as pd
from dateutil.tz import tzlocal

from redengine.conditions import (
    TaskStarted, 

    TaskFinished, 
    TaskFailed, 
    TaskSucceeded,

    TaskRunning
)
from redengine.time import (
    TimeDelta, 
    TimeOfDay
)
from redengine.tasks import FuncTask

def to_epoch(dt):
    # Hack as time.tzlocal() does not work for 1970-01-01
    if dt.tz:
        dt = dt.tz_convert("utc").tz_localize(None)
    return (dt - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

def setup_task_state(mock_datetime_now, logs:List[Tuple[str, str]], time_after=None, task=None):
    """A mock up that sets up a task to test the 
    condition with given logs

    Parameters
    ----------
    tmpdir : Pytest fixture
    mock_datetime_now : Pytest fixture
    logs : list of tuples
        Logs to be inserted for the task.
        The tuple is in form (datetime, action)
    time_after : date-like
        The datetime when inspecting the condition status
    """
    if task is None:
        task = FuncTask(
            lambda:None, 
            name="the task",
            execution="main"
        )

    # pd.Timestamp -> Epoch, https://stackoverflow.com/a/54313505/13696660
    # We also need tz_localize to convert timestamp to localized form (logging thinks the time is local time and convert that to GTM)

    for log in logs:
        log_time, log_action = log[0], log[1]
        log_created = to_epoch(pd.Timestamp(log_time, tz=tzlocal()))
        record = logging.LogRecord(
            # The content here should not matter for task status
            name='redengine.core.task', level=logging.INFO, lineno=1, 
            pathname='redengine\\redengine\\core\\task\\base.py',
            msg="Logging of 'task'", args=(), exc_info=None,
        )

        record.created = log_created
        record.action = log_action
        record.task_name = "the task"

        task.logger.handle(record)

    if time_after is not None:
        mock_datetime_now(time_after)
    return task


@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            True,
            id="Is running"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "run"),
            ],
            "2020-01-01 07:30",
            True,
            id="Is running (multiple times)"),

        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "success"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (succeeded)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "fail"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (failed)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (terminated)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (inacted)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "crash_release"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (crash_release)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [],
            "2020-01-01 07:30",
            False,
            id="Is not running (and has never ran)"),
        pytest.param(
            lambda:TaskRunning(task="the task"), 
            [
                ("2020-01-01 07:50", "run"),
            ],
            "2020-01-01 07:30",
            False,
            id="Is not running (but does in the future)", marks=pytest.mark.xfail(reason="Bug but not likely to encounter")),
    ],
)
def test_running(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session):
    session.config.force_status_from_logs = True
    setup_task_state(mock_datetime_now, logs, time_after)
    cond = get_condition()
    if outcome:
        assert bool(cond)
    else:
        assert not bool(cond)


@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskStarted(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has started"),
        pytest.param(
            lambda:TaskStarted(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:12", "fail"),
                ("2020-01-01 07:12", "success"),
                ("2020-01-01 07:12", "inaction"),
                ("2020-01-01 07:12", "terminate"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has started (also failed, succeeded, terminated & inacted)"),

        pytest.param(
            lambda:TaskStarted(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [],
            "2020-01-02 07:30",
            False,
            id="Not started (at all)"),
        pytest.param(
            lambda:TaskStarted(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:15", "run"),
            ],
            "2020-01-02 07:30",
            False,
            id="Not started (today)"),
        pytest.param(
            lambda:TaskStarted(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:12", "fail"),
                ("2020-01-01 07:12", "success"),
                ("2020-01-01 07:12", "inaction"),
                ("2020-01-01 07:12", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not started (but failed, succeeded, terminated & inacted)"),
    ],
)
def test_started(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session):
    session.config.force_status_from_logs = True
    setup_task_state(mock_datetime_now, logs, time_after)
    cond = get_condition()
    if outcome:
        assert bool(cond)
    else:
        assert not bool(cond)



@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has finished (succeded)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has finished (failed)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has finished (terminated)"),


        # Not
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (only started)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (inacted)"),

        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 00:10", "run"),
                ("2020-01-01 00:20", "success"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (success out of period)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 00:10", "run"),
                ("2020-01-01 00:20", "fail"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (fail out of period)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 00:10", "run"),
                ("2020-01-01 00:20", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (termination out of period)"),
        pytest.param(
            lambda:TaskFinished(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 00:10", "run"),
                ("2020-01-01 00:20", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not finished (inaction out of period)"),
    ],
)
def test_finish(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session):
    session.config.force_status_from_logs = True
    setup_task_state(mock_datetime_now, logs, time_after)
    cond = get_condition()
    if outcome:
        assert bool(cond)
    else:
        assert not bool(cond)


@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has succeeded"),
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
                ("2020-01-01 07:30", "run"),
                ("2020-01-01 07:40", "success"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has succeeded (multiple times)"),

        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
                ("2020-01-01 07:40", "success"),
                ("2020-01-01 07:50", "success"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has succeeded (multiple times oddly)"),

        # Not
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
                ("2020-01-02 07:10", "run"),
                ("2020-01-02 07:20", "success"),
            ],
            "2020-01-03 07:30",
            False,
            id="Not succeeded (today)"),
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not succeeded (only started)"),
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not succeeded (only failed)"),
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not succeeded (only inacted)"),
        pytest.param(
            lambda:TaskSucceeded(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not succeeded (only terminated)"),
            
    ],
)
def test_success(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session):
    session.config.force_status_from_logs = True
    setup_task_state(mock_datetime_now, logs, time_after)
    cond = get_condition()
    if outcome:
        assert bool(cond)
    else:
        assert not bool(cond)


@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has failed"),
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
                ("2020-01-01 07:30", "run"),
                ("2020-01-01 07:40", "fail"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has failed (multiple times)"),

        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
                ("2020-01-01 07:40", "fail"),
                ("2020-01-01 07:50", "fail"),
            ],
            "2020-01-01 07:30",
            True,
            id="Has failed (multiple times oddly)"),

        # Not
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
                ("2020-01-02 07:10", "run"),
                ("2020-01-02 07:20", "fail"),
            ],
            "2020-01-03 07:30",
            False,
            id="Not failed (today)"),
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not failed (only started)"),
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "succeess"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not failed (only succeeded)"),
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not failed (only inacted)"),
        pytest.param(
            lambda:TaskFailed(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Not failed (only terminated)"),
            
    ],
)
def test_fail(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session):
    session.config.force_status_from_logs = True
    setup_task_state(mock_datetime_now, logs, time_after)
    cond = get_condition()
    if outcome:
        assert bool(cond)
    else:
        assert not bool(cond)