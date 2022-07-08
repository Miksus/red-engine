@app.task("daily", execution="main")
def do_unparallel():
    ...

@app.task("daily", execution="thread")
def do_on_separate_thread():
    ...

@app.task("daily", execution="process")
def do_on_separate_process():
    ...