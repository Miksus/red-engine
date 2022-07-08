
import pytest

from redengine.conditions import AlwaysFalse
from redengine.tasks.maintain import ShutDown
from redengine.tasks import FuncTask
from redengine.exc import SchedulerExit
from redengine.core import Scheduler

def write_file(text):
    with open("test.txt", "a") as f:
        f.write(text)

def test_restart_raises(session):
    task = ShutDown()
    with pytest.raises(SchedulerExit):
        task()

def test_scheduler_shutdown(tmpdir, session):

    with tmpdir.as_cwd() as old_dir:
        
        FuncTask(write_file, parameters={"text": "Started"}, on_startup=True, name="write_startup", execution="main")
        FuncTask(write_file, parameters={"text": "Shut"}, on_shutdown=True, name="write_shutdown", execution="main")

        task = ShutDown()

        task.force_run = True
        
        session.config.shut_cond = AlwaysFalse()
        
        session.start()

        with open("test.txt") as f:
            cont = f.read()
        assert "StartedShut" == cont

        records = list(map(lambda e: e.dict(exclude={'created'}), task.logger.get_records()))
        assert 1 == len([record for record in records if record["action"] == "run"])
        assert 1 == len([record for record in records if record["action"] == "success"])
