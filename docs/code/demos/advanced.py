from redengine import RedEngine
from redengine.args import Return, Arg, FuncArg

app = RedEngine()

# Custom Condition
# ----------------

@app.cond('is foo')
def is_foo():
    # This is a custom condition
    ...
    return True

# Parameters
# ----------

app.params(my_arg='Hello')

@app.param('item')
def get_item():
    # This is a custom condition
    ...
    return 'world'

# Tasks
# -----

@app.task('daily', execution="process")
def do_on_process():
    "This task runs once a day and runs on separate process"
    ...
    return ...

@app.task("after task 'do_things'")
def do_pipeline(arg1=Return('do_on_process'), 
                arg2=Arg('item'),
                arg3=Arg('my_arg')):
    """This task runs when 'do_on_process' has succeeded.
    Argument 'arg1' gets the return value of 'do_on_process'
    Argument 'arg2' gets the return value of function 'get_item'
    Argument 'arg3' is simply the value of a session parameter 'my_arg'"""
    ...

@app.task('daily & is foo', execution="thread")
def do_custom():
    """This task runs once a day and when is_foo returns True
    This task runs on separate thread"""
    ...

@app.task('(true & true) | (false & True & ~True)')
def do_complex():
    """Notice the logical expression in the task start condition"""
    ...

if __name__ == "__main__":
    app.run()