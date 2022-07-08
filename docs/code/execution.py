@app.task("daily", execution="main")
def do_main():
    ...

@app.task("daily", execution="thread")
def do_thread():
    ...

@app.task("daily", execution="process")
def do_process():
    ...