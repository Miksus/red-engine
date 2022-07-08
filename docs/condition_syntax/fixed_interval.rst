
.. _cond-fixedinterval:

Fixed time interval
-------------------

**Syntax**

.. code-block:: none

   time of [hour | day | week | month] between <start> and <end>
   time of [hour | day | week | month] [after | before] <time>

**True when**

  When current time is in the given period. 

**Examples**

.. code-block:: python

    app.task("time of hour before 45:00")
    app.task("time of day between 10:00 and 16:00")
    app.task("time of week after Monday")
    app.task("time of month after 5th")

.. warning::
    Be careful for not to use these as your only condition in the 
    ``start_cond``. The task will be rerun constantly during the 
    period.