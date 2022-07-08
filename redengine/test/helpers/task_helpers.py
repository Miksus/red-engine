
import time
TOLERANCE = 2

def wait_till_task_finish(task):
    start = time.time()
    while task.status == "run":
        time.sleep(0.001)
        task.session.scheduler.handle_logs()
        if time.time() - start >= TOLERANCE:
            raise TimeoutError("Task did not finish.")
    task.session.scheduler.handle_logs()