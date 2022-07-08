@app.task("every 10 seconds")
def do_continuously():
    ...

@app.task("daily after 07:00")
def do_daily_after_seven():
    ...

@app.task("hourly & time of day between 22:00 and 06:00")
def do_hourly_at_night():
    ...

@app.task("(weekly on Monday | weekly on Saturday) & time of day after 10:00")
def do_twice_a_week_after_ten():
    ...