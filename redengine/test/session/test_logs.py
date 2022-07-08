
from itertools import chain
import datetime
import logging
from typing import Optional
from pydantic import Field, root_validator

import pytest
import pandas as pd

from redbird.oper import in_, between
from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo

from redengine.log.log_record import LogRecord, TaskLogRecord, MinimalRecord
from redengine.tasks import FuncTask

def create_line_to_startup_file():
    with open("start.txt", "w") as file:
        file.write("line created\n")

def create_line_to_shutdown():
    with open("shut.txt", "w") as file:
        file.write("line created\n")

class CustomRecord(MinimalRecord):
    timestamp: Optional[datetime.datetime]
    start: Optional[datetime.datetime]
    end: Optional[datetime.datetime]
    runtime: Optional[datetime.timedelta]
    message: str

    @root_validator
    def validate_timestamp(cls, values):
        values['timestamp'] = datetime.datetime.fromtimestamp(values['created'])
        return values

@pytest.mark.parametrize(
    "query,expected",
    [
        pytest.param(
            {"action": "run"}, 
            [
                {'task_name': 'task1', 'timestamp': datetime.datetime(2021, 1, 1, 0, 0, 0), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 0, 0, 0), 'message': "Task 'task1' status: 'run'"},
                {'task_name': 'task2', 'timestamp': datetime.datetime(2021, 1, 1, 1, 0, 0), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 1, 0, 0), 'message': "Task 'task2' status: 'run'"},
                {'task_name': 'task3', 'timestamp': datetime.datetime(2021, 1, 1, 2, 0, 0), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'timestamp': datetime.datetime(2021, 1, 1, 3, 0, 0), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            id="Get running"),
        pytest.param(
            {"action": in_(["success", "fail"])}, 
            [
                {'task_name': 'task1', 'created': datetime.datetime(2021, 1, 1, 4, 0, 0).timestamp(), 'action': 'success', 'start': datetime.datetime(2021, 1, 1, 0, 0, 0), 'end': datetime.datetime(2021, 1, 1, 4, 0, 0), 'runtime': datetime.timedelta(hours=4), 'message': "Task 'task1' status: 'success'"},
                {'task_name': 'task2', 'created': datetime.datetime(2021, 1, 1, 5, 0, 0).timestamp(), 'action': 'fail',    'start': datetime.datetime(2021, 1, 1, 1, 0, 0), 'end': datetime.datetime(2021, 1, 1, 5, 0, 0), 'runtime': datetime.timedelta(hours=4), 'message': "Task 'task2' status: 'fail'"},
            ],
            id="get succees & failure"),
        pytest.param(
            {"timestamp": between(pd.Timestamp("2021-01-01 02:00:00"), pd.Timestamp("2021-01-01 03:00:00"))}, 
            [
                {'task_name': 'task3', 'created': datetime.datetime(2021, 1, 1, 2, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'created': datetime.datetime(2021, 1, 1, 3, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            id="get time span (pd.Timestamp)"),
        pytest.param(
            {"timestamp": between(None, pd.Timestamp("2021-01-01 03:00:00"), none_as_open=True), "action": "run"}, 
            [
                {'task_name': 'task1', 'created': datetime.datetime(2021, 1, 1, 0, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 0, 0, 0), 'message': "Task 'task1' status: 'run'"},
                {'task_name': 'task2', 'created': datetime.datetime(2021, 1, 1, 1, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 1, 0, 0), 'message': "Task 'task2' status: 'run'"},
                {'task_name': 'task3', 'created': datetime.datetime(2021, 1, 1, 2, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'created': datetime.datetime(2021, 1, 1, 3, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            id="get time span (pd.Timestamp, open left)"),
        pytest.param(
            {"timestamp": between(pd.Timestamp("2021-01-01 02:00:00"), None, none_as_open=True), "action": "run"}, 
            [
                {'task_name': 'task3', 'created': datetime.datetime(2021, 1, 1, 2, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'created': datetime.datetime(2021, 1, 1, 3, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            id="get time span (pd.Timestamp, open right)"),
        pytest.param(
            {"timestamp": between(None, None, none_as_open=True), "action": "run"}, 
            [
                {'task_name': 'task1', 'created': datetime.datetime(2021, 1, 1, 0, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 0, 0, 0), 'message': "Task 'task1' status: 'run'"},
                {'task_name': 'task2', 'created': datetime.datetime(2021, 1, 1, 1, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 1, 0, 0), 'message': "Task 'task2' status: 'run'"},
                {'task_name': 'task3', 'created': datetime.datetime(2021, 1, 1, 2, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'created': datetime.datetime(2021, 1, 1, 3, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            id="get time span (open left, open right)"),
        pytest.param(
            {"timestamp": between(datetime.datetime(2021, 1, 1, 2, 0, 0), datetime.datetime(2021, 1, 1, 3, 0, 0))}, 
            [
                {'task_name': 'task3', 'created': datetime.datetime(2021, 1, 1, 2, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 2, 0, 0), 'message': "Task 'task3' status: 'run'"},
                {'task_name': 'task4', 'created': datetime.datetime(2021, 1, 1, 3, 0, 0).timestamp(), 'action': 'run', 'start': datetime.datetime(2021, 1, 1, 3, 0, 0), 'message': "Task 'task4' status: 'run'"},
            ],
            marks=pytest.mark.xfail(reason="timerange passed as datetime but datetime is mocked and isinstance fails"),
            id="get time span (datetime)"),
    ],
)
def test_get_logs_params(tmpdir, mock_pydatetime, mock_time, query, expected, session):
    with tmpdir.as_cwd() as old_dir:
        task_logger = logging.getLogger(session.config.task_logger_basename)
        task_logger.handlers = [
            RepoHandler(repo=MemoryRepo(model=CustomRecord))
        ]

        task1 = FuncTask(lambda: None, name="task1", execution="main", force_run=True)
        task2 = FuncTask(lambda: None, name="task2", execution="main", force_run=True)
        task3 = FuncTask(lambda: None, name="task3", execution="main", force_run=True)
        task4 = FuncTask(lambda: None, name="task4", execution="main", force_run=True)

        # Start
        mock_pydatetime("2021-01-01 00:00:00")
        task1.log_running()

        mock_pydatetime("2021-01-01 01:00:00")
        task2.log_running()

        mock_pydatetime("2021-01-01 02:00:00")
        task3.log_running()

        mock_pydatetime("2021-01-01 03:00:00")
        task4.log_running()

        # Action
        mock_pydatetime("2021-01-01 04:00:00")
        task1.log_success()

        mock_pydatetime("2021-01-01 05:00:00")
        task2.log_failure()

        mock_pydatetime("2021-01-01 06:00:00")
        task3.log_inaction()  

        mock_pydatetime("2021-01-01 07:00:00")
        task4.log_termination()  
    
        #scheduler()
        
        logs = session.get_task_log(**query)
        assert isinstance(logs, chain)
        
        logs = list(logs)
        assert len(expected) == len(logs)
        logs = list(map(lambda e: e.dict(), logs))
        for e, a in zip(expected, logs):
            #assert e.keys() <= a.keys()
            # Check all expected items in actual (actual can contain extra)
            for key, val in e.items():
                assert a[key] == e[key]
            # assert e.items() <= a.items()