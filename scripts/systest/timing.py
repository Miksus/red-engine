
# This file contains a whole scheduling
# system. Useful for simple or quick projects.

import logging
import datetime

from redengine import Session
from redengine.tasks import FuncTask
from redengine.arguments import FuncArg
from redengine.extensions import Sequence


# Session
# -------

session = Session(
    scheme=["log_memory"] # Logging to memory, customize as needed.
)

# Logging
# -------

# You may want to customize the logging.
# You can just add new handlers to the 
# task/scheduler logging, like:

# Creating a new handler
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
default_stream = logging.StreamHandler()
default_stream.setFormatter(formatter)
default_stream.setLevel(logging.INFO)

# Setting the handler 
sched_logger = logging.getLogger(session.config["scheduler_logger_basename"])
sched_logger.addHandler(default_stream)


# Tasks
# -----

# Feel free to delete/modify as you wish.

@FuncTask(start_cond="minutely", execution="main")
def minutely():
    print(f"Executing minutely {datetime.datetime.now()}")
    ...

@FuncTask(start_cond="hourly", execution="main")
def hourly():
    print(f"Executing hourly {datetime.datetime.now()}")
    ...

@FuncTask(start_cond="daily", execution="main")
def daily():
    print(f"Executing daily {datetime.datetime.now()}")
    ...

@FuncTask(start_cond="weekly", execution="main")
def weekly():
    print(f"Executing weekly {datetime.datetime.now()}")
    ...

# Starting up
# -----------
if __name__ == "__main__":
    session.start()