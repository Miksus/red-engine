
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
from redengine.conditions.task import TaskInacted, TaskTerminated
from redengine.time import (
    TimeDelta, 
    TimeOfDay
)
from redengine.tasks import FuncTask

from .test_time import setup_task_state

def to_epoch(dt):
    # Hack as time.tzlocal() does not work for 1970-01-01
    if dt.tz:
        dt = dt.tz_convert("utc").tz_localize(None)
    return (dt - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskRunning, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_not_used_false(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    logs = [
        ("2021-01-01 12:00:00", state)
        for state in ("success", "fail", "run", "terminate", "inaction")
    ]
    setup_task_state(mock_datetime_now, logs, task=task)
    cond = cls(task=task)
    assert not cond

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskRunning, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_not_used_true(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    for attr in ("last_run", "last_success", "last_fail", "last_inaction", "last_terminate"):
        setattr(task, attr, pd.Timestamp("2000-01-01 12:00:00"))
    cond = cls(task=task)
    assert cond

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskRunning, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_not_used_true_inside_period(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    for attr in ("last_run", "last_success", "last_fail", "last_inaction", "last_terminate"):
        setattr(task, attr, pd.Timestamp("2000-01-01 12:00:00"))
    cond = cls(task=task, period=TimeOfDay("07:00", "13:00"))
    mock_datetime_now("2000-01-01 14:00")
    assert bool(cond)

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_not_used_false_outside_period(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    for attr in ("last_run", "last_success", "last_fail", "last_inaction", "last_terminate"):
        setattr(task, attr, pd.Timestamp("2000-01-01 05:00:00"))
    cond = cls(task=task, period=TimeOfDay("07:00", "13:00"))
    mock_datetime_now("2000-01-01 14:00")
    assert not cond

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_not_used_equal_zero(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    logs = [
        ("2021-01-01 12:00:00", state)
        for state in ("success", "fail", "run", "terminate", "inaction")
    ]
    setup_task_state(mock_datetime_now, logs, task=task)
    cond = cls(task=task) == 0
    assert cond

@pytest.mark.parametrize("cls",
    [
        TaskFailed, TaskSucceeded, TaskFinished, TaskStarted, TaskInacted, TaskTerminated
    ]
)
def test_logs_used(session, cls, mock_datetime_now):
    session.config.force_status_from_logs = False
    
    task = FuncTask(
        lambda:None, 
        name="the task",
        execution="main"
    )
    logs = [
        ("2021-01-01 12:00:00", state)
        for state in ("success", "fail", "run", "terminate", "inaction")
    ]
    setup_task_state(mock_datetime_now, logs, task=task)
    # Only the latest status is stored
    # thus one cannot determine whether the task has run percisely once
    # without looking to logs.
    mock_datetime_now("2021-01-01 14:00")
    if cls is TaskFinished:
        cond = cls(task=task) == 3
    else:
        cond = cls(task=task) == 1 
    assert cond
