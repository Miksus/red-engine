
import logging

import pytest
import pandas as pd
from dateutil.tz import tzlocal

from redengine.conditions import (
    TaskExecutable,
)
from redengine.time import (
    TimeDelta, 
    TimeOfDay
)
from redengine.tasks import FuncTask

@pytest.mark.parametrize("from_logs", [pytest.param(True, id="from logs"), pytest.param(False, id="optimized")])
@pytest.mark.parametrize(
    "get_condition,logs,time_after,outcome",
    [
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-01 07:30",
            False,
            id="Don't run (already succeeded)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-01 07:30",
            False,
            id="Don't run (already failed)"),
    
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Don't run (terminated)"),
    
        pytest.param(
            # Termination is kind of failing but retry is not applicable as termination is often
            # indication that the task is not desired to be run anymore (as it has already taken
            # enough system resources)
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00"), retries=1), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-01 07:30",
            False,
            id="Don't run (terminated with retries)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-01 08:30",
            False,
            id="Don't run (already ran and out of time)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2021-12-31 08:30",
            False,
            id="Don't run (missed)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-02 06:00",
            False,
            id="Don't run (not yet time)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [],
            "2020-01-01 08:30",
            False,
            id="Don't run (out of time and not run at all)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "inaction"),
            ],
            "2020-01-01 07:30",
            False,
            id="Do not run (has inacted)"), # One would not want the task to try to run every millisecond if inacted.

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
            ],
            "2020-01-01 07:30",
            False,
            id="Do not run (is already running)", marks=pytest.mark.xfail(reason="Bug but does not affect if no multiple schedulers nor multilaunch allowed")), # One would not want the task to try to run every millisecond if inacted.

        # Do run
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [],
            "2020-01-01 07:10",
            True,
            id="Do run (has not run at all)"),
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00"), retries=1), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-01 07:30",
            True,
            id="Do run (has retries)"),
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "success"),
            ],
            "2020-01-02 07:30",
            True,
            id="Do run (succeeded yesterday)"),
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "fail"),
            ],
            "2020-01-02 07:30",
            True,
            id="Do run (failed yesterday)"),
        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "terminate"),
            ],
            "2020-01-02 07:30",
            True,
            id="Do run (terminated yesterday)"),

        pytest.param(
            lambda:TaskExecutable(task="the task", period=TimeOfDay("07:00", "08:00")), 
            [
                ("2020-01-01 07:10", "run"),
                ("2020-01-01 07:20", "inaction"),
            ],
            "2020-01-02 07:30",
            True,
            id="Do run (inacted yesterday)"),

    ],
)
def test_executable(tmpdir, mock_datetime_now, logs, time_after, get_condition, outcome, session, from_logs):
    session.config.force_status_from_logs = from_logs
    def to_epoch(dt):
        # Hack as time.tzlocal() does not work for 1970-01-01
        if dt.tz:
            dt = dt.tz_convert("utc").tz_localize(None)
        return (dt - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    with tmpdir.as_cwd() as old_dir:

        
        task = FuncTask(
            lambda:None, 
            name="the task",
            execution="main"
        )

        condition = get_condition()

        # pd.Timestamp -> Epoch, https://stackoverflow.com/a/54313505/13696660
        # We also need tz_localize to convert timestamp to localized form (logging thinks the time is local time and convert that to GTM)

        for log in logs:
            log_time, log_action = log[0], log[1]
            log_created = to_epoch(pd.Timestamp(log_time, tz=tzlocal()))
            record = logging.LogRecord(
                # The content here should not matter for task status
                name='redengine.core.task', level=logging.INFO, lineno=1, 
                pathname='d:\\Projects\\redengine\\redengine\\core\\task\\base.py',
                msg="Logging of 'task'", args=(), exc_info=None,
            )

            record.created = log_created
            record.action = log_action
            record.task_name = "the task"

            task.logger.handle(record)
            setattr(task, f'last_{log_action}', pd.Timestamp(log_time))
        mock_datetime_now(time_after)

        if outcome:
            assert bool(condition) 
        else:
            assert not bool(condition)
