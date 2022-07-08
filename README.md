
# <span style="color:red">Red</span> Engine
> Powering your Python Apps

-----------------

[![Pypi version](https://badgen.net/pypi/v/redengine)](https://pypi.org/project/redengine/)
[![build](https://github.com/Miksus/red-engine/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/Miksus/red-engine/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/Miksus/red-engine/branch/master/graph/badge.svg?token=U2KF1QA5HT)](https://codecov.io/gh/Miksus/red-engine)
[![Documentation Status](https://readthedocs.org/projects/red-engine/badge/?version=latest)](https://red-engine.readthedocs.io/en/latest/?badge=latest)
[![PyPI pyversions](https://badgen.net/pypi/python/redengine)](https://pypi.org/project/redengine/)

## What is it?

Red Engine is a modern scheduling framework for Python 
applications. It is simple, clean and extensive. It is 
the engine that sets your Python programs alive.

The library is minimal on the surface but extensive 
and customizable underneath. The syntax very clean:

```python
from redengine import RedEngine

app = RedEngine()

@app.task('daily')
def do_daily():
    ...

if __name__ == '__main__':
    app.run()
```

Compared to alternatives, Red Engine has perhaps the most elegant syntax and is the most productive. It offers more features than Crontab or APScheduler but is much
easier to work with than Airflow. It does not make assumptions of your project.

Read more from the documentations: [Red Engine, documentations](https://red-engine.readthedocs.io/en/stable/)

## Installation

Install Red Engine from [PyPI](https://pypi.org/project/redengine/):

```shell
pip install redengine
```


## More Examples?

**Scheduling:**

```python
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
```

**Pipelining tasks:**

```python
from redengine.args import Return

@app.task("daily after 07:00")
def do_first():
    ...
    return 'Hello World'

@app.task("after task 'do_first'")
def do_second(arg=Return('do_first')):
    # arg contains the value of the task do_first's return
    ...
    return 'Hello Python'
```

**Parallelizing tasks:**

```python
@app.task("daily", execution="main")
def do_unparallel():
    ...

@app.task("daily", execution="thread")
def do_on_separate_thread():
    ...

@app.task("daily", execution="process")
def do_on_separate_process():
    ...
```

---

## Author

* **Mikael Koli** - [Miksus](https://github.com/Miksus) - koli.mikael@gmail.com

