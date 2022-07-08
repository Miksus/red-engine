
from typing import Dict, List, Callable, Tuple
import inspect

class _Hooker:
    # No, this is not what you think.

    def __init__(self, hooks:List[Callable], args:Tuple=None, kwargs:Dict=None):
        self.args = () if args is None else args
        self.kwargs = {} if kwargs is None else kwargs
        self.hooks = hooks
    
    def prerun(self, *args, **kwargs):
        self._post_hooks = []
        for hook in self.hooks:
            result = hook(*args, **kwargs)
            if inspect.isgeneratorfunction(hook):
                gener = result
                next(gener, None) # Executes first yield
                self._post_hooks.append(gener)

    def postrun(self, *args):
        for gener in self._post_hooks:
            try:
                gener.send(args)
            except StopIteration:
                pass

    def __enter__(self):
        self.prerun()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.postrun()


def clear_hooks():
    "Remove all hooks."
    from redengine.core import Task, Scheduler
    Task.init_hooks = []
    Scheduler.startup_hooks = []
    Scheduler.cycle_hooks = []
    Scheduler.shutdown_hooks = []