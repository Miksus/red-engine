
.. _condition-syntax:

Condition Syntax
================

This section lists the pre-built condition syntax that are 
allowed to be passed as strings to ``start_cond``
or ``end_cond`` of a task.

.. note::

  You can also combine multiple conditions using 
  logical operators:
  
  - ``&``: AND operator
  - ``|``: OR operator 
  - ``~`` NOT operator 
  
  For example: ``(daily | after task 'mytask') & ~time of day after 10:00``


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   execution
   fixed_interval
   timedelta
   task_status
   dependence

Explanations of the syntax notation:

* ``<start>``, ``<end>`` and ``<time>``: These are fixed time components
    
    * if "hour", use format mm:ss, ie. ``30:00`` (half past)
    * if "day", use 24 hour clock, ie. ``14:00`` (2 PM)
    * if "week", supply weekdays as full names or abbreviations, ie. ``Monday`` or ``Mon``
    * if "month", supply a day of month, ie. ``13th`` (13th of month)

* ``<timedelta>``: These are time deltas

    * Supply timedelta as sting, ie. ``1 days, 30 min``. See  `pandas.Timedelta <https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html>`_.

* ``<task>``: These are names of tasks

    * Supply a name of a task. The task can be created later but should be created before inspecting the status of the condition.