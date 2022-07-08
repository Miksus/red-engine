@app.task('every 10 seconds')
def do_constantly():
    ...

@app.task('every 1 minute')
def do_minutely():
    ...

@app.task('every 1 hour')
def do_hourly():
    ...

@app.task('every 1 day')
def do_daily():
    ...

@app.task('every 2 days 2 hours 20 seconds')
def do_custom():
    ...