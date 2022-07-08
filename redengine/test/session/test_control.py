
import pytest

from redengine.args import Session
import redengine
from redengine.conditions.scheduler import SchedulerStarted
from redengine.conditions import TaskStarted
from redengine.core.time.base import TimeDelta
from redengine.tasks import FuncTask
from redengine.conditions import true


@pytest.mark.parametrize("execution", ["main", "thread"])
def test_shutdown(execution, session):
    timeline = []

    def on_startup():
        timeline.append("startup")

    def call_shutdown(session:redengine.Session=Session()):
        session.shutdown()
        timeline.append("shutdown-called")

    def on_shutdown():
        timeline.append("shutdown")


    FuncTask(on_startup, name="startup", on_startup=True, start_cond=true, execution=execution, session=session)
    FuncTask(call_shutdown, name="call-shutdown", start_cond=true, execution=execution, session=session)
    FuncTask(on_shutdown, name="shutdown", on_shutdown=True, start_cond=true, execution=execution, session=session)


    session.config.shut_cond = TaskStarted(task="call-shutdown") >= 3

    session.start()
    assert timeline == ['startup', 'shutdown-called', 'shutdown']

@pytest.mark.parametrize("execution", ["main", "thread"])
def test_restart(execution, session):
    timeline = []
    session.config.restarting = 'recall'

    def on_startup():
        timeline.append("startup")

    def call_restart(session:redengine.Session=Session()):
        session.restart()
        timeline.append("restart-called")

    def on_shutdown():
        timeline.append("shutdown")

    FuncTask(on_startup, name="startup", on_startup=True, execution="main", session=session)
    FuncTask(call_restart, name="restart", start_cond=true, execution=execution, session=session)
    FuncTask(on_shutdown, name="shutdown", on_shutdown=True, execution="main", session=session)

    session.config.shut_cond = (TaskStarted(task="shutdown") >= 2) | ~SchedulerStarted(period=TimeDelta("60 second"))

    session.start()
    assert timeline == ['startup', 'restart-called', 'shutdown', 'startup', 'restart-called', 'shutdown', 'startup', 'shutdown']