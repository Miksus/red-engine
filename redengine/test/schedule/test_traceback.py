
import logging

import pytest
import pandas as pd
from redengine.conditions.scheduler import SchedulerStarted
from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo
from redengine.core.time.base import TimeDelta

from redengine.log.log_record import LogRecord
from redengine.core import Scheduler
from redengine.core.time.base import TimeDelta
from redengine.tasks import FuncTask
from redengine.conditions import TaskStarted, AlwaysTrue

def run_failing():
    raise RuntimeError("Task failed")

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_task_fail_traceback(tmpdir, execution, session):
    # There is a speciality in tracebacks in multiprocessing
    # See: https://bugs.python.org/issue34334

    # TODO: Delete. This has been handled now in test_core.py
    with tmpdir.as_cwd() as old_dir:
        task_logger = logging.getLogger(session.config.task_logger_basename)
        task_logger.handlers = [
            RepoHandler(repo=MemoryRepo(model=LogRecord))
        ]
        task = FuncTask(run_failing, name="task", start_cond=AlwaysTrue(), execution=execution)

        session.config.shut_cond = (TaskStarted(task="task") >= 3) | ~SchedulerStarted(period=TimeDelta("5 seconds"))
        session.start()
        
        failures = list(task.logger.get_records(action="fail"))
        assert 3 == len(failures)

        for record in failures:
            tb = record.exc_text
            assert "Traceback (most recent call last):" in tb
            assert "RuntimeError: Task failed" in tb
