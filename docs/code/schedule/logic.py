@app.task('true & false')
def do_never():
    ...

@app.task('true | false')
def do_constantly():
    ...

@app.task('~false')
def do_constantly_2():
    ...