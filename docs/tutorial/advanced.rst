.. _advanced-guide:

Advanced Guide
==============

This is an advanced level tutorial.

App Configuration
-----------------

There are several configurations options
for the application. 

The configurations can be set by:

.. code-block:: python

    app = RedEngine(config={
        'task_execution': 'process',
        'task_pre_exist': 'raise',
        'force_status_from_logs': True,

        'silence_task_prerun': False,
        'silence_cond_check': False,

        'max_process_count': 5,
        'restarting': 'replace'
    })

These are the default options. 

- **task_execution**: How tasks are run by default. Options: 

    - process: on separate process
    - thread: on separate thread
    - main: no parallelization

- **task_pre_exist**: What happens if a task with given name already exists. Options:

    - ``raise``: An error is thrown
    - ``rename``: the task is renamed (numbers added after the name)
    - ``ignore``: The task is simply not inserted to the session

- **force_status_from_logs**: Use logs always to determine the task statuses. If:

    - ``True``: Logs are always read when checking the statuses. Robust but less performant.
    - ``False``: If cached status found, it is used instead.

- **silence_task_prerun**: Whether to silence errors occurred before running a task. If:

    - ``True``: The scheduler does not crash on errors occurred on the startup of a task
    - ``False``: The scheduler crashes. Useful for debug but not for production
    
- **silence_cond_check**: Whether to silence errors occurred when checking conditions' values. If:

    - ``True``: The scheduler does not crash on errors occurred on checking conditions
    - ``False``: The scheduler crashes. Useful for debug but not for production

- **max_process_count**: Maximum number of processes allowed to be started

    - By default the number of CPUs

- **restarting**: How the scheduler is restarted (if restart is called)

    - ``replace``: Restart by replacing the current process
    - ``relaunch``: Restart by starting a new process
    - ``fresh``: Restart by starting a new process (on new window on Windows)
    - ``recall``: Restart by calling the start method again. Useful for testing the restart


Task Types
----------

So far, we have only used ``FuncTask`` with passing a callable.
There are other task types as well to cover most common use cases:

- ``FuncTask``: Executes a Python function
- ``CommandTask``: Executes a shell command
- ``CodeTask``: Executes raw code as string. Potentially dangerous.

Here are the ways to initialize tasks:

.. code-block:: python

    @app.task('daily')
    def do_things():
        ...

    def run_things():
        ...
    
    app.task('daily', func=run_things)

    app.task('daily', func_name="main", path="path/to/example.py")

    app.task('daily', command='echo "Hello world"')

    app.task('daily', code='print("Hello world")')


Modifying the System on Runtime
-------------------------------

The scheduler system can be modified in runtime.
You could during the runtime:

- shut down the scheduler
- restart the scheduler
- force a task to be run
- disable a task
- create, update or delete tasks

To do there, you can create a task that
runs either as a separate thread or on 
the main loop. Tasks parallelized as 
separate processes cannot alter the 
scheduling environment due to limitations 
with sharing memory. 

To alter the session:

.. code-block:: python

    from redengine.args import Session

    @app.task('every 20 hours', execution="thread")
    def do_shutdown(session=Session()):
        session.shutdown()

    @app.task('every 20 hours', execution="thread")
    def do_restart(session=Session()):
        session.restart()

    @app.task('every 10 minutes', execution="thread")
    def do_modify_tasks(session=Session()):

        task = session['do_restart']
        task.force_run = True

        for task in session.tasks:
            task.disable = True

    