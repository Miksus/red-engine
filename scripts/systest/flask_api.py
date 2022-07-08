
# This file contains a whole scheduling
# system. Useful for simple or quick projects.

import logging

from redengine import Session
from redengine.tasks import FuncTask
from redengine.arguments import FuncArg
from redengine.tasks.api import FlaskAPI


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
task_logger = logging.getLogger(session.config["task_logger_basename"])
sched_logger = logging.getLogger(session.config["scheduler_logger_basename"])
task_logger.addHandler(default_stream)
sched_logger.addHandler(default_stream)


# Tasks
# -----

# Feel free to delete/modify as you wish.

@FuncTask(start_cond="minutely")
def my_pytask_1():
    print(f"Executing 'my_pytask_1'...")
    ...

@FuncTask(start_cond="minutely", name="my_pytask_2")
def my_pytask_2(my_session_arg):
    print(f"Executing 'my_pytask_2' with session param '{my_session_arg}'...")
    ...

@FuncTask(start_cond="minutely", name="my_pytask_3", parameters={"my_param": "a task arg"})
def do_stuff_1(my_param):
    print(f"Executing 'my_pytask_3' with task param '{my_param}'...")
    ...

@FuncTask(start_cond="minutely") # after task 'my_pytask_1'
def my_pytask_4():
    print(f"Executing 'my_pytask_4' that depends on 'my_task_1'...")
    ...

@FuncTask(name="my_pytask_5")
def my_pytask_5():
    print(f"Executing 'my_pytask_5' that depends on 'my_task_2' using Sequence...")
    ...

@FuncTask(start_cond="every 5 sec", name="metatask", execution="thread")
def do_meta_stuff():
    print(f"Executing meta task that can operate on the session. (Disables itself)")
    session.tasks["metatask"].disabled = True
    ...


# Arguments
# ---------

@FuncArg.to_session()
def my_session_arg():
    print("Getting session argument...")
    ...
    return 'a session arg'


FlaskAPI(app_config={'JSONIFY_PRETTYPRINT_REGULAR': True})

# Starting up
# -----------
if __name__ == "__main__":
    session.start()