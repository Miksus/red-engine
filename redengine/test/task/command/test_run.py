
import logging
from pathlib import Path
import platform
import sys

import pytest

from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo

from redengine.log.log_record import LogRecord
from redengine.tasks import CommandTask

from task_helpers import wait_till_task_finish

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
@pytest.mark.parametrize("cmd,params,systems,shell", [
    pytest.param(["python", "-c", "open('test.txt', 'w');"], None, ["win32"], False, id="list (win32)"),
    pytest.param("python -c \"open('test.txt', 'w');\"", None, ["win32"], False, id="string (win32)"),
    pytest.param(["python"], {"c": "open('test.txt', 'w')"}, ["win32"], False, id="list with params (win32)"),
    pytest.param("python", {"c": "open('test.txt', 'w')"}, ["win32"], False, id="string with params (win32)"),

    pytest.param(["python3", "-c", "open('test.txt', 'w');"], None, ["linux", "linux2"], False, id="list (linux)"),
    pytest.param("python3 -c \"open('test.txt', 'w');\"", None, ["linux", "linux2"], True, id="string (linux)"),
    pytest.param(["python3"], {"c": "open('test.txt', 'w')"}, ["linux", "linux2"], False, id="list with params (linux)"),
    pytest.param("python3", {"c": "open('test.txt', 'w')"}, ["linux", "linux2"], True, id="string with params (linux)"),
])
def test_success_command(tmpdir, session, cmd, params, systems,shell, execution):
    if systems is not None and sys.platform not in systems:
        pytest.skip("Command not supported by OS")
    with tmpdir.as_cwd() as old_dir:
        assert not Path("test.txt").is_file()

        task = CommandTask(
            command=cmd, 
            name="a task",
            shell=shell,
            execution="main",
            parameters=params,
            argform="short"
        )
        assert task.status is None

        task()
        wait_till_task_finish(task)

        assert Path("test.txt").is_file()
        assert "success" == task.status

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_fail_command(tmpdir, execution, session):
    with tmpdir.as_cwd() as old_dir:

        task_logger = logging.getLogger(session.config.task_logger_basename)
        task_logger.handlers = [
            RepoHandler(repo=MemoryRepo(model=LogRecord))
        ]

        task = CommandTask(
            command=["python", "--not_an_arg"], 
            name="a task",
            shell=False,
            execution=execution
        )
        assert task.status is None

        task()

        wait_till_task_finish(task)

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert "fail" == task.status

        err = records[1]["exc_text"].strip().replace('\r', '')
        if (sys.version_info.major, sys.version_info.minor) >= (3, 8):
            expected = "OSError: Failed running command (2): \nunknown option --not_an_arg\nusage: python [option] ... [-c cmd | -m mod | file | -] [arg] ...\nTry `python -h' for more information."
        else:
            expected = "OSError: Failed running command (2): \nUnknown option: --\nusage: python [option] ... [-c cmd | -m mod | file | -] [arg] ...\nTry `python -h' for more information."
        assert err.endswith(expected)

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_success_bat_file(tmpdir, execution, session):
    if platform.system() != "Windows":
        pytest.skip("Bat files only runnable on Windows.")

    with tmpdir.as_cwd() as old_dir:
        assert not Path("test.txt").is_file()

        file = tmpdir.join("my_command.bat")
        file.write('python -c "{code}"'.format(code="open('test.txt', 'w');"))

        task = CommandTask(
            command=["my_command.bat"], 
            name="a task",
            shell=False,
            execution="main"
        )
        assert task.status is None

        task()
        wait_till_task_finish(task)

        assert Path("test.txt").is_file()
        assert "success" == task.status


def test_success_bash_file(tmpdir, session):
    if platform.system() == "Windows":
        pytest.skip("Bash files not runnable on Windows.")
        
    with tmpdir.as_cwd() as old_dir:
        assert not Path("test.txt").is_file()

        file = tmpdir.join("my_command.sh")
        file.write('python3 -c "{code}"'.format(code="open('test.txt', 'w');"))

        task = CommandTask(
            command=["/bin/bash", "my_command.sh"], 
            name="a task",
            shell=False,
            execution="main"
        )
        assert task.status is None

        task()
        wait_till_task_finish(task)

        assert Path("test.txt").is_file()
        assert "success" == task.status