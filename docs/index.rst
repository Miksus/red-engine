
.. meta::
   :description: Red Engine, modern scheduling framework
   :keywords: schedule, task, script, run, Python

:red:`Red` Engine
=================

.. image:: https://badgen.net/pypi/v/redengine
   :target: https://pypi.org/project/redengine/

.. image:: https://badgen.net/pypi/python/redengine
   :target: https://pypi.org/project/redengine/

.. raw:: html

   <hr>

No time to read? :ref:`Get started then. <getting-started>`

Red Engine is a modern scheduling framework for Python 
applications. It is simple, clean and extensive.

**Key features:**

- Simple: productive and easy to set up
- Clean: Scheduling is just plain English
- Robust: Well tested and production ready
- Extensive: Has a lot of built-in features
- Customizable: Designed to be modified

**Core functionalities:**

- Powerful scheduling syntax
- Task parallelization
- Task parametrization
- Task pipelining
- Modifiable session also in runtime

**It looks like this:**

.. literalinclude:: /code/demos/minimal.py
    :language: py

Why Red Engine?
---------------

There are a lot of options for scheduler:

- Crontab
- APScheduler
- Airflow

Red Engine provides more features than Crontab and APScheduler
and it is much easier to use than Airflow. Red Engine
has by far the cleanest syntax compared to the alternatives and it is 
the most productive.

Red Engine is not meant to be the scheduler for enterprise pipelines,
unlike Airflow, but it is fantastic to power your Python applications.

Here is a demonstration of more advanced case:

.. literalinclude:: /code/demos/intermediate.py
    :language: py


Interested?
-----------

Just install the library:

.. code-block:: console

    pip install redengine

There is much more to offer. See :ref:`quick start <getting-started>`
And the rest :ref:`tutorials <tutorials>`.


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   tutorial/index
   condition_syntax/index
   examples/index
   how_it_works
   contributing
   versions


Indices and tables
==================

* :ref:`genindex`
