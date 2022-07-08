
import logging
from textwrap import dedent
import pytest

from redbird.logging import RepoHandler
from redbird.repos import MemoryRepo

from redengine.log.log_record import LogRecord
from redengine.tasks import CodeTask
from redengine.core import Scheduler
from redengine.conditions import TaskStarted

def test_construct(session):
    task = CodeTask(code=dedent("""
        def main():
            ...
        main()
        """), start_cond="daily", name="mytask")
    assert task.name == "mytask"
    assert "mytask" in session

def test_construct_missing_name(session):
    with pytest.raises(ValueError):
        task = CodeTask(code=dedent("""
            def main():
                ...
            main()
            """))

@pytest.mark.parametrize('execution', ['main', 'thread', 'process'])
def test_run_success(session, execution):
    
    task = CodeTask(code=dedent("""
        def main():
            return 'myvalue'

        return_value = main()
        """), execution=execution, name="mytask")
    task.force_run = True

    session.config.shut_cond = TaskStarted(task='mytask') >= 1
    session.start()
    assert task.status == 'success'
    assert session.returns[task] == 'myvalue'

@pytest.mark.parametrize('execution', ['main', 'thread', 'process'])
def test_run_success_parametrize(session, execution):
    
    task = CodeTask(code=dedent("""
        def main(param):
            return 'myvalue' + param

        return_value = main(myparam)
        """), name="mytask", execution=execution, parameters={'myparam': ' + myparam'})
    task.force_run = True

    session.config.shut_cond = TaskStarted(task='mytask') >= 1
    session.start()

    assert task.status == 'success'
    assert session.returns[task] == 'myvalue + myparam'

@pytest.mark.parametrize('execution', ['main', 'thread', 'process'])
def test_run_fail(session, execution):
    
    task_logger = logging.getLogger(session.config.task_logger_basename)
    task_logger.handlers = [
        RepoHandler(repo=MemoryRepo(model=LogRecord))
    ]

    task = CodeTask(code=dedent("""
        def main():
            raise RuntimeError('Failed')

        return_value = main()
        """), execution=execution, name="mytask")
    task.force_run = True

    session.config.shut_cond = TaskStarted(task='mytask') >= 1
    session.start()
    
    assert task.status == 'fail'

    records = list(map(lambda e: e.dict(exclude={'created'}), session.get_task_log()))
    record_fail = [r for r in records if r['action'] == 'fail'][0]
    assert 'File "<string>", line 5, in <module>\n  File "<string>", line 3, in main\nRuntimeError: Failed' in record_fail['exc_text']