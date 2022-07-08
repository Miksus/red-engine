
from redengine.tasks.func import FuncTask
from textwrap import dedent
import pytest
import pandas as pd

from redengine.tasks import FuncTask

from task_helpers import wait_till_task_finish


@pytest.mark.parametrize("execution", ["main", "thread", "process"])
@pytest.mark.parametrize(
    "script_path,expected_outcome,exc_cls",
    [
        pytest.param(
            "scripts/succeeding_script.py", 
            "success",
            None,
            id="Success"),
        pytest.param(
            "scripts/failing_script.py", 
            "fail", 
            RuntimeError,
            id="Failure"),
        pytest.param(
            "scripts/syntax_error_script.py", 
            "fail", 
            ImportError,
            id="Import failure"),
    ],
)
def test_run(tmpdir, script_files, script_path, expected_outcome, exc_cls, execution, session):
    session.config.silence_task_prerun = True
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path=script_path, 
            name="a task",
            execution=execution
        )
        try:
            task()
        except:
            if not exc_cls:
                raise

        wait_till_task_finish(task)

        assert task.status == expected_outcome

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": expected_outcome},
        ] == records


def test_run_specified_func(tmpdir, session):
    task_dir = tmpdir.mkdir("mytasks")
    task_dir.join("myfile.py").write(dedent("""
    def myfunc():
        pass
    """))

    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="myfunc",
            path="mytasks/myfile.py", 
            name="a task",
            execution="main"
        )
        task()

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records


def test_import_relative(tmpdir, session):
    task_dir = tmpdir.mkdir("mytasks")
    task_dir.join("myfile.py").write(dedent("""
    from utils import value
    def main():
        assert value == 5
    """))

    task_dir.join("utils.py").write(dedent("""
    value = 5
    """))

    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="mytasks/myfile.py", 
            name="a task",
            execution="main"
        )
        task()

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_import_package(tmpdir, session):
    pkg_dir = tmpdir.mkdir("mypkg6574")
    sub_dir = pkg_dir.mkdir("subpkg")
    util_dir = pkg_dir.mkdir("utils")

    pkg_dir.join("__init__.py").write("")
    sub_dir.join("__init__.py").write("")
    util_dir.join("__init__.py").write("from .util_file import value")

    sub_dir.join("myfile.py").write(dedent("""
    from mypkg6574.utils import value
    def main():
        assert value == 5
    """))

    util_dir.join("util_file.py").write("value = 5")

    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="mypkg6574/subpkg/myfile.py", 
            name="a task",
            execution="main"
        )
        task()

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_import_relative_with_params(tmpdir, session):
    task_dir = tmpdir.mkdir("mytasks")
    task_dir.join("myfile.py").write(dedent("""
    from utils import value
    def main(val_5, optional=None):
        assert val_5 == 5
        assert optional is None
    """))

    task_dir.join("utils.py").write(dedent("""
    value = 5
    """))

    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="mytasks/myfile.py", 
            name="a task",
            execution="main"
        )
        task(params={"val_5":5})

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_additional_sys_paths(tmpdir, session):
    task_dir = tmpdir.mkdir("mytasks")
    task_dir.join("myfile.py").write(dedent("""
    from utils import value
    # "utils" is in subfolder/utils.py but it is put to sys.path

    def main(val_5, optional=None):
        assert val_5 == 5
        assert optional is None
    """))

    task_dir.mkdir("subfolder").mkdir("another").join("utils.py").write(dedent("""
    value = 5
    """))

    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="mytasks/myfile.py", 
            name="a task",
            execution="main",
            sys_paths=["mytasks/subfolder/another"]
        )
        task(params={"val_5":5})

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

# Parametrization
def test_parametrization_runtime(tmpdir, script_files, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="scripts/parameterized_script.py", 
            name="a task",
            execution="main"
        )

        task(params={"integer": 1, "string": "X", "optional_float": 1.1, "extra_parameter": "Should not be passed"})

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_parametrization_local(tmpdir, script_files, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="scripts/parameterized_script.py", 
            name="a task",
            parameters={"integer": 1, "string": "X", "optional_float": 1.1},
            execution="main"
        )

        task()

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records

def test_parametrization_kwargs(tmpdir, script_files, session):
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            func_name="main",
            path="scripts/parameterized_kwargs_script.py", 
            name="a task",
            parameters={"integer": 1, "string": "X", "optional_float": 1.1},
            execution="main"
        )

        task()

        records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
        assert [
            {"task_name": "a task", "action": "run"},
            {"task_name": "a task", "action": "success"},
        ] == records