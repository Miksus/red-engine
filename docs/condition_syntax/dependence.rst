
.. _cond-dependence:

Task Dependence
---------------

**Syntax**

.. code-block:: none

   after task '<task>'
   after task '<task>' [succeeded | failed | finished | terminated]
   after tasks '<task 1>', '<task 2>' ... 
   after tasks '<task 1>', '<task 2>' ... [succeeded | failed | finished]
   after any tasks '<task 1>', '<task 2>' ... [succeeded | failed | finished]

**True when**

  True if the assigned task has not run after the given task has
  succeeded/failed/finished/terminated. Useful for creating 
  task pipelines.

.. note::

  Must be assigned to a task.


**Examples**

.. code-block:: python

    # Creating a dummy task
    @app.task()
    def a_task():
        ...
    
    # Examples
    app.task("after task 'a_task'")
    app.task("after task 'a_task' succeeded")
    app.task("after task 'a_task' failed")
    app.task("after task 'a_task' finished")
    app.task("after tasks 'a_task', 'another_task' finished")