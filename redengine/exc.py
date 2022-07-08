class SchedulerRestart(Exception):
    "Restart the scheduler"


class SchedulerExit(Exception):
    "Shut down the scheduler"


class TaskInactionException(Exception):
    "Task did not succeed nor fail. It did not need to run."


class TaskTerminationException(Exception):
    """Task was terminated.
    This should only be raised by threaded
    tasks to signal that they did indeed
    listen the thread_please_terminate event
    and ended as a result of that"""