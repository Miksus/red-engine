from redengine.core import BaseCondition, Task

from redengine.session import Session, Config
from redengine.parse import add_condition_parser
from redengine.conditions import true, false
from redengine.tasks import CommandTask, FuncTask, CodeTask
from redengine.tasks.maintain import ShutDown, Restart
from redengine.tasks.maintain import Restart

from redengine.conditions.meta import _FuncTaskCondWrapper

def _setup_defaults():
    "Set up the task classes and conditions Redengine provides out-of-the-box"
    
    # Add some extra parsers from core 
    add_condition_parser({
        "true": true,
        "false": false,
        "always false": false,
        "always true": true
    })

    # Update type hints
    cls_tasks = (
        Task,
        FuncTask, CommandTask, CodeTask,
        ShutDown, Restart,

        _FuncTaskCondWrapper
    )
    for cls_task in cls_tasks:
        cls_task.update_forward_refs(Session=Session, BaseCondition=BaseCondition)

    Config.update_forward_refs(BaseCondition=BaseCondition)
    #Session.update_forward_refs(
    #    Task=Task, Parameters=Parameters, Scheduler=Scheduler
    #)