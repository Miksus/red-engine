.. _basic-tutorial:

Basic Tutorial
==============

This is a basic level tutorial.

Topics of the tutorial:

- Time scheduling
- Execution options
- Changing log destination

Time Scheduling
---------------

There are a lot of scheduling options in Red Engine:
the tasks can run at specific time, after some other 
tasks have run or when other conditions are met. In 
this tutorial we focus on the time specific scheduling
as that is most used. In later tutorials we discuss 
other options.

.. literalinclude:: /code/schedule/time_of.py
    :language: py

You may also schedule tasks to run on fixed time 
periods (ie. daily, weekly, monthly):

.. literalinclude:: /code/schedule/fixed_period.py
    :language: py


But what if you wanted to schedule to run on
specific time on those periods? That's also easy:

.. literalinclude:: /code/schedule/fixed_period_with_args.py
    :language: py


Our previous examples were scheduled to run once in the
time periods we specified. There are also ``time of ...``
scheduling options for situations in which you wish 
to run the task constantly in the given period or 
if you wish to add them to other scheduling options 
(we get back to this later):

.. code-block:: python

    @app.task('time of day between 10:00 and 18:00')
    def do_constantly_during_day():
        ...

    @app.task('time of week between Saturday and Sunday')
    def do_constantly_during_weekend():
        ...


Execution Options
-----------------

There are three options for how tasks are executed:

- ``process``: Run the task in a separate process
- ``thread``: Run the task in a separate thread
- ``main``: Run the task in the main process and thread (default)

Here is a quick example of each:

.. literalinclude:: /code/execution.py
    :language: py

You may also put the default execution method
if there is one that you prefer in your project:

.. code-block:: python

    app = RedEngine(config={'task_execution': 'main'})

    @app.task("daily")
    def do_main():
        ...

There are pros and cons in each option. In short:

=========== =============  =====================  ========================
Execution   Parallerized?  Can be terminated?      Can modify the session?
=========== =============  =====================  ========================
``process`` Yes            Yes                    No
``thread``  Yes            Yes if task supports   Yes
``main``    No             No                     Yes
=========== =============  =====================  ========================


Changing Logging Destination
----------------------------

Logging the states of the tasks is vital for Red Engine's system.
This includes the logs about when each task started, succeeded 
and failed. This information is used in many of the scheduling 
statements and to prevent setting the same task running multiple
times.

Red Engine extends `logging library's <https://docs.python.org/3/library/logging.html>`_ 
loggers extending them with `Red Bird <https://red-bird.readthedocs.io/>`_
to enable reading the logs. 

By default, the logs are stored in-memory and they do not 
persist over if the scheduler is restarted. You may change 
the destination simply by creating a Red Bird repo and 
pass that as the ``logger_repo`` to the application.

**Storing the logs in-memory:**

.. code-block:: python

    from redengine import RedEngine
    from redbird.repos import MemoryRepo

    app = RedEngine(
        logger_repo=MemoryRepo()
    )

**Storing the logs to CSV file:**

.. code-block:: python

    from redengine import RedEngine
    from redbird.repos import CSVFileRepo

    app = RedEngine(
        logger_repo=CSVFileRepo(
            filename="logs.csv"
        )
    )

See more repos from `Red Bird documentation <https://red-bird.readthedocs.io/>`_.
We will get back on customizing the loggers in later tutorials.