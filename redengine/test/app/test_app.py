
import logging

from redengine import RedEngine
from redengine.conditions.task.task import TaskStarted
from redengine.args import Return, Arg, FuncArg
from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo, CSVFileRepo

from redengine import Session
from redengine.tasks import CommandTask
from redengine.tasks import FuncTask

def set_logging_defaults():
    task_logger = logging.getLogger("redengine.task")
    task_logger.handlers = []
    task_logger.setLevel(logging.WARNING)

def test_app_create(session, tmpdir):
    set_logging_defaults()

    app = RedEngine()

    # Test logging
    task_logger = logging.getLogger("redengine.task")
    
    # Till Red Bird supports equal, we need to test the handler one obj at a time
    assert len(task_logger.handlers) == 1
    assert isinstance(task_logger.handlers[0], RepoHandler)
    assert isinstance(task_logger.handlers[0].repo, MemoryRepo)

    assert isinstance(app.session, Session)

    # Test setting SQL repo
    with tmpdir.as_cwd():
        app = RedEngine(logger_repo=CSVFileRepo(filename="myrepo.csv"))
    assert len(task_logger.handlers) == 2
    assert isinstance(task_logger.handlers[0], RepoHandler)
    assert isinstance(task_logger.handlers[0].repo, CSVFileRepo)

    assert isinstance(app.session, Session)

def test_app_tasks():
    set_logging_defaults()

    app = RedEngine(config={'task_execution': 'main'})

    # Creating some tasks
    @app.task('daily')
    def do_func():
        ...
        return 'return value'

    app.task('daily', name="do_command", command="echo 'hello world'")
    app.task('daily', name="do_script", path=__file__)

    # Assert and test tasks
    assert len(app.session.tasks) == 3

    assert isinstance(app.session['do_func'], FuncTask)
    assert isinstance(app.session['do_command'], CommandTask)
    assert isinstance(app.session['do_script'], FuncTask)

def test_app_run():
    set_logging_defaults()

    # Creating app
    app = RedEngine(config={'task_execution': 'main'})
    app.params(my_arg='session value')

    # Creating some params and conditions 
    @app.param('my_func_arg')
    def my_func():
        return 'func arg value'

    @app.cond('is foo')
    def is_foo():
        return True

    # Creating some tasks
    @app.task('daily & is foo')
    def do_daily():
        ...
        return 'return value'
    
    @app.task("after task 'do_daily'")
    def do_after(arg=Return('do_daily'), session_arg=Arg('my_arg'), func_arg=Arg('my_func_arg'), func_arg_2=FuncArg(lambda: 'my val')):
        assert arg == 'return value'
        assert session_arg == 'session value'
        assert func_arg == 'func arg value'
        assert func_arg_2 == 'my val'

    @app.task("true")
    def do_fail():
        raise

    @app.task("false", execution='process', name="never done", parameters={'arg_1': 'something'})
    def do_never(arg_1):
        raise

    app.session.config.shut_cond = TaskStarted(task='do_after')

    # Testing the app has all relevant things
    session = app.session
    assert 'is foo' in list(session._cond_parsers)
    assert set(task.name for task in session.tasks) == {'do_daily', 'do_after', 'do_fail', 'never done'}

    app.run()

    logger = app.session['do_after'].logger
    assert logger.filter_by(action="success").count() == 1

    logger = app.session['do_fail'].logger
    assert logger.filter_by(action="fail").count() == 1

    # Test the parameters are passed to a task
    task_example = session['never done']
    assert task_example.execution == 'process'
    assert task_example.name == 'never done'
    assert dict(task_example.parameters) == {'arg_1': 'something'}