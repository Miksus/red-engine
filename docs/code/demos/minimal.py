from redengine import RedEngine

app = RedEngine()

@app.task('daily')
def do_things():
    ...

if __name__ == "__main__":
    app.run()