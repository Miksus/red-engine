from redengine import RedEngine
from redengine.args import Return

app = RedEngine()

@app.task('daily')
def do_daily():
    "This function runs once a day"
    ...

@app.task('daily between 07:00 and 10:00 | daily between 16:00 and 20:00')
def do_twice_a_day():
    "This function runs twice a day (in the morning and in the afternoon)"
    # The '|' means OR operator. Fully supports logical operations.
    ...

@app.task("after task 'do_daily'")
def do_after_another(arg=Return('do_daily')):
    "Run after 'do_daily' task"
    # The parameter 'arg' has the return value of the function 'do_daily'
    ...

if __name__ == "__main__":
    # Start the scheduler
    app.run()