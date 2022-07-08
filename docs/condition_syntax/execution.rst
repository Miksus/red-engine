
.. _cond-execution:

Execution on fixed time interval
--------------------------------

**Syntax**

.. code-block:: none

   [hourly | daily | weekly | monthly]
   [hourly | daily | weekly | monthly] between <start> and <end>
   [hourly | daily | weekly | monthly] [before | after | starting] <time>

**True when**

  When current time is in the given period and the task 
  has not yet run in the given period.

.. note::

  Must be assigned to a task (is a ``start_cond`` of a task).

**Examples**

.. code-block:: python

    app.task("hourly")
    app.task("daily between 22:00 and 23:00")
    app.task("weekly before Friday")
    app.task("monthly starting 3rd")