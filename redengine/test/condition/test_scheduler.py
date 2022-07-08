
import datetime

from redengine.conditions import (
    SchedulerStarted,
    SchedulerCycles
)
from redengine.time import (
    TimeDelta, 
    TimeOfDay
)

def test_scheduler_cycles(session):

    session.config.shut_cond = SchedulerCycles(_eq_=3)
    session.start()
    # Imitating the __bool__
    assert bool(SchedulerCycles(_eq_=3))
    assert bool(SchedulerCycles(_gt_=2))
    assert bool(SchedulerCycles(_lt_=4))
    assert bool(SchedulerCycles(_ne_=4))
    assert not bool(SchedulerCycles(_lt_=3))
    assert not bool(SchedulerCycles(_gt_=3))
    assert not bool(SchedulerCycles(_eq_=4))


def test_scheduler_started(session):

    session.scheduler.startup_time = datetime.datetime.now() - datetime.timedelta(0, 20, 0) # 20 seconds ago
    # Imitating the __bool__
    assert bool(SchedulerStarted(period=TimeDelta("30 seconds")))
    assert not bool(SchedulerStarted(period=TimeDelta("10 seconds")))
