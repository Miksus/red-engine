
from pathlib import Path
import types

import pytest

from redengine.tasks import FuncTask
from redengine.conditions import AlwaysFalse, AlwaysTrue, DependSuccess
from redengine.parse.utils import ParserError

def myfunc(): ...

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_construct(tmpdir, session, execution):

    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        if execution == "process":
            with pytest.raises(AttributeError):
                # Unpicklable function (cannot use process)
                task = FuncTask(lambda : None, execution=execution)
        else:
            task = FuncTask(lambda : None, execution=execution)
            
        # This should always be picklable
        task = FuncTask(myfunc, execution=execution)
        assert not task.is_delayed()
        assert task.status is None

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_construct_callable_class(tmpdir, session, execution):
    class MyClass:
        def __call__(self):
            pass

    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        # This should always be picklable
        task = FuncTask(MyClass(), execution=execution)
        assert not task.is_delayed()
        assert task.status is None
        assert task.name.endswith("test_construct:MyClass")

def test_description(session):
    "Test Task.description is correctly set (uses the func if missing)"

    # Test no description
    task = FuncTask(name="no desc 1")
    @task
    def myfunc():
        ...
    assert task.description is None

    task = FuncTask(lambda x: x, name="no desc 2", execution="main")
    assert task.description is None


     # Test description from doc (decorated)
    task = FuncTask(name="has desc 1")
    @task
    def myfunc():
        "This is func"
    assert task.description == "This is func"

    # Test description from doc (normal)
    def myfunc():
        "This is func"
    task = FuncTask(myfunc, name="has desc 2")
    assert task.description == "This is func"

    # Test the description is respected if doc is found
    def myfunc():
        "This is func"
    task = FuncTask(myfunc, name="has desc 3", description="But this is preferred")
    assert task.description == "But this is preferred"

    # Test the description is respected if doc missing
    def myfunc():
        ...
    task = FuncTask(myfunc, name="has desc 4", description="This is func")
    assert task.description == "This is func"

@pytest.mark.parametrize("execution", ["main", "thread", "process"])
def test_construct_delayed(tmpdir, session, execution):

    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:
        task = FuncTask(func_name="myfunc", path="myfile.py", execution=execution)
        assert task.status is None
        assert task.is_delayed()
        assert task.func_name == "myfunc"
        assert task.path == Path("myfile.py")
        assert task.func is None

def test_construct_decorate(tmpdir, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:


        @FuncTask(start_cond=AlwaysTrue(), name="mytask", execution="main")
        def do_stuff():
            pass
        
        assert isinstance(do_stuff, types.FunctionType)

        do_stuff_task = session["mytask"]
        assert isinstance(do_stuff_task, FuncTask)
        assert do_stuff_task.status is None
        assert do_stuff_task.start_cond == AlwaysTrue()
        assert do_stuff_task.name == "mytask"

        assert {do_stuff_task} == session.tasks 

def test_construct_decorate_minimal(tmpdir, session):
    """This is an exception when FuncTask returns itself 
    (__init__ cannot return anything else)"""
    # Going to tempdir to dump the log files there
    orig_default_exec = session.config.task_execution
    session.config.task_execution = 'main'
    try:
        with tmpdir.as_cwd() as old_dir:

            @FuncTask
            def do_stuff():
                pass

            assert isinstance(do_stuff, FuncTask)
            assert do_stuff.status is None
            assert do_stuff.start_cond == AlwaysFalse()
            assert do_stuff.name.endswith(":do_stuff")

            assert {do_stuff} == session.tasks
    finally:
        session.config.task_execution = orig_default_exec

def test_construct_decorate_default_name(tmpdir, session):
    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:


        @FuncTask(start_cond=AlwaysTrue(), execution="main")
        def do_stuff():
            pass
        
        assert isinstance(do_stuff, types.FunctionType)
        do_stuff_task = list(session.tasks)[-1]
        assert isinstance(do_stuff_task, FuncTask)
        assert do_stuff_task.status is None
        assert do_stuff_task.start_cond == AlwaysTrue()
        assert do_stuff_task.name.endswith(":do_stuff")

        assert [do_stuff_task] == list(session.tasks)

@pytest.mark.parametrize(
    "start_cond,depend,expected",
    [
        pytest.param(
            AlwaysTrue(),
            None,
            AlwaysTrue(),
            id="AlwaysTrue"),
    ],
)
def test_set_start_condition(tmpdir, start_cond, depend, expected, session):

    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None, 
            name="task",
            start_cond=start_cond,
            execution="main",
        )
        assert expected == task.start_cond


@pytest.mark.parametrize(
    "start_cond_str,start_cond",
    [
        pytest.param("true", lambda: AlwaysTrue(), id="true"),
        pytest.param("always true & always true", lambda: AlwaysTrue() & AlwaysTrue(), id="always true & always true"),
    ],
)
def test_set_start_condition_str(tmpdir, start_cond_str, start_cond, session):

    # Going to tempdir to dump the log files there
    with tmpdir.as_cwd() as old_dir:

        task = FuncTask(
            lambda : None, 
            name="task",
            start_cond=start_cond_str,
            execution="main",
        )
        assert start_cond() == task.start_cond

        assert str(task.start_cond) == start_cond_str

@pytest.mark.parametrize(
    "get_task,exc",
    [
        pytest.param(
            lambda: FuncTask(lambda : None, name="task", start_cond="this is not valid", execution="main"), 
            ParserError, 
            id="invalid start_cond"
        ),
        pytest.param(
            lambda: FuncTask(lambda : None, name="task", execution="not valid"), 
            ValueError, 
            id="invalid execution"
        ),
    ],
)
def test_failure(session, exc, get_task):
    with pytest.raises(exc):
        get_task()
    assert session.tasks == set()

def test_rename(session):
    task1 = FuncTask(lambda : None, name="a task 1", execution="main")
    task2 = FuncTask(lambda : None, name="a task 2", execution="main")
    assert session.tasks == {task1, task2}
    assert 'renamed task' not in session
    assert 'a task 1' in session

    task1.name = "renamed task"
    assert task1.name == "renamed task"
    assert session.tasks == {task1, task2}
    assert 'renamed task' in session
    assert 'a task 1' not in session

def test_rename_conflict(session):
    task1 = FuncTask(lambda : None, name="a task 1", execution="main")
    task2 = FuncTask(lambda : None, name="a task 2", execution="main")
    assert session.tasks == {task1, task2}
    assert 'renamed task' not in session
    assert 'a task 1' in session

    with pytest.raises(ValueError):
        task1.name = "a task 2"
    assert session.tasks == {task1, task2}
    assert session['a task 2'] is task2
    assert session['a task 2'] is not task1

def test_existing_raise(session):
    assert session.config.task_pre_exist == 'raise'

    task1 = FuncTask(lambda : None, name="a task", execution="main")
    with pytest.raises(ValueError):
        task2 = FuncTask(lambda : None, name="a task", execution="main")
    assert session.tasks == {task1}

def test_existing_ignore(session):
    session.config.task_pre_exist = 'ignore'
    task1 = FuncTask(lambda : None, name="a task", execution="main")
    task2 = FuncTask(lambda : None, name="a task", execution="main")
    assert session.tasks == {task1}

@pytest.mark.skip(reason="No support for this yet")
def test_existing_replace(session):
    session.config.task_pre_exist = 'replace'
    task1 = FuncTask(lambda : None, name="a task", execution="main")
    task2 = FuncTask(lambda : None, name="a task", execution="main")
    assert session.tasks == {"a task": task2}

def test_existing_rename(session):
    session.config.task_pre_exist = 'rename'
    task1 = FuncTask(lambda : None, name="a task", execution="main")
    task2 = FuncTask(lambda : None, name="a task", execution="main")
    assert session.tasks == {task1, task2}
    assert task2.name == 'a task - 1'

    assert session['a task'] is task1
    assert session['a task - 1'] is task2