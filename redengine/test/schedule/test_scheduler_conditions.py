
from redengine.core import Scheduler
from redengine.time import TimeDelta
from redengine.conditions import SchedulerCycles, SchedulerStarted

def test_scheduler_started(tmpdir, session):
    with tmpdir.as_cwd() as old_dir:

        session.config.shut_cond = ~SchedulerStarted(period=TimeDelta("1 second"))
        session.start()

        assert session.scheduler.n_cycles > 1

def test_scheduler_cycles(tmpdir, session):
    with tmpdir.as_cwd() as old_dir:

        session.config.shut_cond = SchedulerCycles() >= 4
        session.start()

        assert session.scheduler.n_cycles == 4