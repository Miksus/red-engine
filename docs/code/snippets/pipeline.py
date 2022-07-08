from redengine.args import Return

@app.task("daily after 07:00")
def do_first():
    ...
    return 'Hello World'

@app.task("after task 'do_first'")
def do_second(arg=Return('do_first')):
    # arg contains the value of the task do_first's return
    ...
    return 'Hello Python'
