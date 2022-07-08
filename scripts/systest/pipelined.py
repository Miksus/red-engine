
from redengine.tasks import FuncTask
from redengine.arguments import Return
from redengine import session

#session = Session(scheme="log_simple")
#session.config['task_execution'] = 'main'

@FuncTask(start_cond='every 10 seconds')
def task_a():
    print("Running task_a")
    return "a's value"

@FuncTask(start_cond="after task 'task_a'", parameters={'a_value': Return('task_a')})
def task_b(a_value):
    print("Running task_b")
    assert a_value == "a's value"
    return "b's value"

@FuncTask(start_cond="after tasks 'task_a', 'task_b'", parameters={'a_value': Return('task_a'), 'b_value': Return('task_b')})
def task_c(a_value, b_value):
    print("Running task_c")
    assert a_value == "a's value"
    assert b_value == "b's value"
    return "c's value"

if __name__ == '__main__':
    print("Starting")
    session.start()