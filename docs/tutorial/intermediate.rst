.. _intermediate-tutorial:

Intermediate Tutorial
=====================

This is an intermediate level tutorial.

Condition Logic
----------------

Previously we have introduced some ways to schedule tasks.
Sometimes the existing options are not enough and you need
to compose a scheduling logic from multiple conditions. 
For such purpose, there are logical operations:

- ``&``: *AND* operator 
- ``|``: *OR* operator 
- ``~``: *NOT* operator

Using these are pretty simple:

.. literalinclude:: /code/schedule/logic.py
    :language: py

We used conditions ``true`` and ``false`` but you 
may replace these with other conditions (ie. ``daily``) 
from previous examples.

You may also add parentheses for extra logic:

.. code-block:: python

    @app.task('(true & false) | (~false)')
    def do_constantly():
        ...

Scheduling strings may become quite long some times.
The strings can also be broken down to multiple lines:

.. code-block:: python

    @app.task('''
        daily between 07:00 and 10:00
        & (time of week on Monday | time of week on Friday)
    ''')
    def do_on_monday_or_friday_morning():
        ...


Pipelining with Conditions
--------------------------

Tasks can also be piped by setting a task to 
run after another, setting a output of a task
as the input for another or both. 

.. literalinclude:: /code/snippets/pipeline.py
    :language: py

The second task runs when the first has succeeded
and the input argument gets the value of the output
argument of the first task.

Parameterize Tasks
------------------

Parameters are key-value pairs passed to the tasks.
The value of the pair is called *argument*. The 
argument can be derived from the return of another 
task, from the return value of a function or 
a component of the scheduling framework.

There are also two scopes of parameters: session level
and task level. When a task is run, the argument is 
looked from the task level arguments and then from the 
session level arguments.

Here is an illustration:

.. code-block:: python

    from redengine.args import Arg

    # Setting arguments to the session
    app.params(
        my_arg='Hello world'
    )

    @app.task("every 10 seconds")
    def do_things(item = Arg('my_arg')):
        ...

We set a session level argument (``my_arg``)
and we used that in the task ``do_things``. 
The session level argument is turned as a 
task level argument with ``Arg('my_arg'`)``.
This argument can be reused in multiple tasks
as it was set on session level. 

Setting an argument to task level only looks like 
this:

.. code-block:: python

    from redengine.args import SimpleArg

    @app.task("every 10 seconds")
    def do_things(item = SimpleArg('Hello world')):
        ...

``SimpleArg`` is just a placeholder argument that 
is simply the value that was passed (which is 
``'Hello world'``). In the example above the argument
is not reusable in other tasks.

Next we will cover some basic argument types that 
have more functionalities.

Function Argments
^^^^^^^^^^^^^^^^^

Function arguments are arguments which values are 
derived from the return value of a function. To 
set a session level function argument:

.. code-block:: python

    from redengine.args import FuncArg

    def get_item():
        return 'hello world'

    @app.task("every 10 seconds")
    def do_things(item = FuncArg(get_item)):
        ...

To set task level function argument:

.. code-block:: python

    from redengine.args import Arg

    @app.param('my_arg')
    def get_item():
        return 'hello world'

    @app.task("every 10 seconds")
    def do_things(item = Arg('my_arg')):
        ...

Meta Argments
^^^^^^^^^^^^^

Meta arguments are arguments that contain 
a component of the scheduling system.
These are useful when you need to manipulate
the session in a task (ie. shut down the 
scheduler or add/delete tasks) or manipulate
some tasks (ie. force running or change 
attributes).

An example of the session argument:

.. code-block:: python

    from redengine.args import Session

    @app.task("every 10 seconds")
    def manipulate_session(session = Session()):
        ...

An example of the task argument:

.. code-block:: python

    from redengine.args import Task

    @app.task("every 10 seconds")
    def manipulate_task(this_task=Task(), another_task = Task('do_things')):
        ...

Customizing Logging Handlers
----------------------------

Red Engine uses `Red Bird's <https://red-bird.readthedocs.io/>`_
`logging handler <https://red-bird.readthedocs.io/en/latest/logging_handler.html>`_
for implementing a logger that can be read programmatically.
Red Bird is a repository pattern library that abstracts 
database access from application code. This is helpful 
to create a unified interface to read the logs regardless
if they are stored to a CSV file, SQL database or to 
a plain Python list in memory.

As the logger is simply extension of `the logging library <https://docs.python.org/3/library/logging.html>`_,
you may add other logging handlers as well: 

.. code-block:: python

    import logging
    from redengine import RedEngine

    app = RedEngine()

    # Create a handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Add the handler
    task_logger = logging.getLogger('redengine.task')
    task_logger.addHandler(handler)

.. warning::

    Make sure the logger ``redengine.task`` has at least 
    one ``redbird.logging.RepoHandler`` in handlers or 
    the system cannot read the log information.

Reading from the Logs
---------------------

Reading programmatically from the logs is easy due to unified 
querying syntax of Red Bird.

Simply 

.. code-block:: python

    import logging
    
    task_logger = logging.getLogger('redengine.task')

    # Getting a RepoHandler
    for handler in task_logger.handlers:
        if hasattr(handler, "repo"):
            break
    
    # Query all logs from the handler
    handler.filter_by().all()

Read more about the querying from `Red Bird's documentation <https://red-bird.readthedocs.io/en/latest/>`_