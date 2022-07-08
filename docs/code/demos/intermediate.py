from redengine import RedEngine
from redengine.args import Return, Arg, FuncArg

app = RedEngine()

@app.cond('is foo')
def is_foo():
    "This is a custom condition"
    ...
    return True


@app.task('daily & is foo', execution="process")
def do_daily():
    "This task runs once a day and runs on separate process"
    ...
    return ...

@app.task("after task 'do_daily'")
def do_after(arg1=Return('do_daily')):
    """This task runs after 'do_daily' and it has its the 
    return argument as an input"""
    ...


if __name__ == "__main__":
    app.run()