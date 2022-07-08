
import pickle
import pytest
from redengine.tasks import FuncTask



def test_to_dict(session):
    task1 = FuncTask(func=lambda: None, name="task 1", start_cond="every 10 seconds")
    task2 = FuncTask(func=lambda: None, name="task 2", start_cond="after task 'task 1'")

    task1.dict()
    task2.dict()

    task1.json()
    task2.json()
    pass