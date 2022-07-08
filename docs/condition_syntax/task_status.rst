
.. _cond-status:

Task Status
-----------

**Syntax**

.. code-block:: none

   has [succeeded | failed | finished | started | terminated] [this hour | today | this week | this month] between <start> and <end>
   has [succeeded | failed | finished | started | terminated] [this hour | today | this week | this month] [before | after] <time>
   has [succeeded | failed | finished | started | terminated] past <timedelta>

**True when**
  
  True if the assigned task has succeeded/failed/started/terminated inside the given period.

.. note::

  Must be assigned to a task.


**Examples**

.. code-block:: python

    app.task("has succeeded this hour")
    app.task("has failed today between 08:00 and 16:00")
    app.task("has started this week before Friday")
    app.task("has terminated this month after 6th")
    app.task("has succeeded past 2 hours, 30 minutes")