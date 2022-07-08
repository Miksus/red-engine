
from redengine.tasks import CommandTask

def test_construct():
    task = CommandTask(command="echo 'hello world'")
    assert "echo 'hello world'" == task.command