from redengine import RedEngine
from redengine.args import Arg
from redmail import EmailSender

app = RedEngine()
app.params(receivers=['me@example.com'])
email = EmailSender(
    host="smtp.myserver.com", port=584,
    username="me@example.com", password="<PASSWORD>"
)

@app.task('hourly')
def measure_performance(receivers):
    email.send(
        subject="Wake up",
    )

@app.task('daily between 10:00 and 12:00')
def eat_lunch(receivers):
    email.send(
        subject="Go to eat",
    )

@app.task('daily between 22:00 and 04:00')
def go_to_sleep(receivers):
    email.send(
        subject="Go to eat",
    )

if __name__ == "__main__":
    app.run()