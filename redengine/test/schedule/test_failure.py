
import datetime
import time
import os, re
import multiprocessing

import pytest
import pandas as pd

import redengine
from redengine import Session
from redengine.conditions.task import TaskFailed
from redengine.core import Scheduler, Parameters
from redengine.core import BaseCondition
from redengine.tasks import FuncTask
from redengine.time import TimeDelta
from redengine.exc import TaskInactionException
from redengine.conditions import SchedulerCycles, SchedulerStarted, TaskStarted, AlwaysFalse, AlwaysTrue
from redengine.core import BaseArgument

class FailingArgument(BaseArgument):

    def __init__(self, fail_in):
        self.fail_in = fail_in

    def stage(self, **kwargs):
        if self.fail_in == "stage":
            raise RuntimeError("Deliberate failure")
        return self

    def get_value(self, **kwargs):
        if self.fail_in == "get_value":
            raise RuntimeError("Deliberate failure")


class FailingCondition(BaseCondition):
    __register__ = False
    def __bool__(self):
        raise RuntimeError("Deliberate failure")

def do_stuff():
    ...

def do_stuff_with_arg(arg):
    ...

@pytest.mark.parametrize(
    "execution,fail_in", [
        pytest.param("main", "get_value", id="main"), 

        pytest.param("thread", "get_value", id="thread, get_value"), 
        pytest.param("thread", "stage", id="thread, stage"), 

        pytest.param("process", "get_value", id="process, get_value"), 
        pytest.param("process", "stage", id="process, stage"), 
    ]
)
def test_param_failure(tmpdir, execution, session, fail_in):
    session.config.silence_task_prerun = True # Prod setting
    task = FuncTask(do_stuff_with_arg, name="a task", parameters={"arg": FailingArgument(fail_in)}, start_cond=AlwaysTrue(), execution=execution)

    session.config.shut_cond = (TaskStarted(task="a task") >= 1) | ~SchedulerStarted(period=TimeDelta("5 second"))
    session.start()
    assert task.status == "fail"

    records = list(map(lambda d: d.dict(exclude={'created'}), task.logger.get_records()))
    assert [{"task_name": "a task", "action": "run"}, {"task_name": "a task", "action": "fail"}] == records

@pytest.mark.parametrize(
    "execution,fail_in", [
        pytest.param("main", "get_value", id="main"), 

        pytest.param("thread", "get_value", id="thread, get_value"), 
        pytest.param("thread", "stage", id="thread, stage"), 

        pytest.param("process", "get_value", id="process, get_value"), 
        pytest.param("process", "stage", id="process, stage"), 
    ]
)
def test_session_param_failure(tmpdir, execution, session, fail_in):
    session.config.silence_task_prerun = True # Prod setting
    session.parameters["arg"] = FailingArgument(fail_in)

    task = FuncTask(do_stuff_with_arg, name="a task", start_cond=AlwaysTrue(), execution=execution)

    session.config.shut_cond = (TaskStarted(task="a task") >= 1) | ~SchedulerStarted(period=TimeDelta("5 second"))
    session.start()
    assert task.status == "fail"
    
    records = list(map(lambda d: d.dict(exclude={'created'}), task.logger.get_records()))
    assert [{"task_name": "a task", "action": "run"}, {"task_name": "a task", "action": "fail"}] == records



@pytest.mark.parametrize(
    "execution,fail_in", [
        pytest.param("main", "get_value", id="main"), 

        pytest.param("thread", "get_value", id="thread, get_value", marks=pytest.mark.xfail(reason="exception relying via thread not implemented")), 
        pytest.param("thread", "stage", id="thread, stage"), 

        pytest.param("process", "get_value", id="process, get_value", marks=pytest.mark.xfail(reason="exception relying via queue not implemented")), 
        pytest.param("process", "stage", id="process, stage"), 
    ]
)
def test_raise_param_failure(tmpdir, execution, session, fail_in):
    session.config.silence_task_prerun = False
    task = FuncTask(do_stuff_with_arg, name="a task", parameters={"arg": FailingArgument(fail_in)}, start_cond=AlwaysTrue(), execution=execution)
    session.config.shut_cond = (TaskStarted(task="a task") >= 1) | ~SchedulerStarted(period=TimeDelta("5 second"))
    
    with pytest.raises(RuntimeError):
        session.start()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_raise_cond_failure(tmpdir, execution, session):
    session.config.silence_cond_check = False
    task = FuncTask(do_stuff, name="a task", start_cond=FailingCondition(), execution=execution)


    session.config.shut_cond = ~SchedulerStarted(period=TimeDelta("5 second"))
    
    with pytest.raises(RuntimeError):
        session.start()

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_silence_cond_failure(tmpdir, execution, session):
    session.config.silence_cond_check = True
    task = FuncTask(do_stuff, name="a task", start_cond=FailingCondition(), execution=execution)

    session.config.shut_cond = shut_cond=SchedulerCycles() >= 3
    session.start()

    assert task.status is None