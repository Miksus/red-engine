from redengine.args import Arg

@app.param('my_param')
def get_my_param():
    "Get a session level parameter"
    return 'Hello world'

@app.task("daily")
def do_with_param(arg=Arg('my_param')):
    # 'arg' 
    assert arg == 'Hello world'
    ...
