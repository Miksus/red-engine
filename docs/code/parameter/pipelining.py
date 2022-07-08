from redengine.args import Return

@app.task("every 10 seconds")
def do_things():
    ...
    return 'hello'

@app.task("after task 'do_things'")
def do_after(arg=Return('do_things')):
    ...
    assert arg == 'hello'
    return 'world'

@app.task("after task 'do_things', 'do_stuff'")
def do_after_all(arg1=Return('do_things'), arg2=Return('do_stuff')):
    ...
    assert arg1 == 'hello'
    assert arg2 == 'world'
