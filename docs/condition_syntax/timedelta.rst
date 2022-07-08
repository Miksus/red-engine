
.. _cond-timedelta:

Timedelta
---------

**Syntax**

.. code-block:: none

    every <timedelta>

**True when**

  When the assigned task has not run inside the timedelta
  (ie. past 1 hour) from current time.

.. note::

  Must be assigned to a task (is a ``start_cond`` of a task).


**Examples**

.. code-block:: python

    app.task("every 1 hour")
    app.task("every 30 sec")
    app.task("every 2 hours, 30 minutes")
    app.task("every 1 day, 12 hour, 30 min, 20 sec")