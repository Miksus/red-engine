@app.task('daily after 10:00')
def do_daily_after():
    ...

@app.task('daily before 22:00')
def do_daily_after():
    ...

@app.task('daily between 10:00 and 22:00')
def do_daily_between():
    ...


@app.task('weekly on Monday')
def do_on_monday():
    ...

@app.task('weekly between Saturday and Sunday')
def do_on_weekend():
    ...


@app.task('monthy after 5th')
def do_monthly_after_fifth():
    ...

@app.task('monthy before 5th')
def do_monthly_before_fifth():
    ...