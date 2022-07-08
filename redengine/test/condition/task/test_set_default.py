
import pytest

from redengine.conditions import (
    TaskFinished, 
    TaskFailed, 
    TaskSucceeded,
)
from redengine.core.condition import set_statement_defaults
from redengine.tasks import FuncTask



def run_task(fail=False):
    print("Running func")
    if fail:
        raise RuntimeError("Task failed")

@pytest.mark.parametrize("cls", [TaskFinished, TaskSucceeded, TaskFailed], ids=["TaskFinished", "TaskSucceeded", "TaskFailed"])
def test_task_set_default(tmpdir, cls, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        task = FuncTask(
            run_task, 
            name="a task"
        )

        condition = cls()
        set_statement_defaults(condition, task=task.name)
        assert condition.kwargs["task"] == task.name

        # Test not
        condition = cls()
        set_statement_defaults(~condition, task=task.name)
        assert condition.kwargs["task"] == task.name

@pytest.mark.parametrize("oper", ["__and__", "__or__"], ids=["&", "|"])
def test_task_set_default_nested(tmpdir, oper, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        base_cond = TaskFinished(task="nondefault")
        conditions = [
            TaskFinished(),
            TaskSucceeded(),
            TaskFailed(),
        ]

        for cond in conditions:
            base_cond = getattr(base_cond, oper)(cond)

        task = FuncTask(
            run_task, 
            name="a task"
        )

        set_statement_defaults(base_cond, task=task.name)

        for i, cond in enumerate(base_cond):
            if i == 0:
                assert cond.kwargs["task"] == "nondefault"
            else:
                assert cond.kwargs["task"] == task.name


def test_task_set_default_nested_deep(tmpdir, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        base_cond = TaskFinished(task="nondefault")
        
        finished1 = TaskFinished()
        failed1 = TaskFailed()
        succeed1 = TaskSucceeded()
        finished_pre_set = TaskFinished(task="predefined")

        condition = finished1 & ((failed1 & ~succeed1) | finished_pre_set)

        task = FuncTask(
            run_task, 
            name="a task"
        )

        set_statement_defaults(condition, task=task.name)
        assert finished1.kwargs["task"] == task.name
        assert failed1.kwargs["task"] == task.name
        assert succeed1.kwargs["task"] == task.name
        assert finished_pre_set.kwargs["task"] == "predefined"