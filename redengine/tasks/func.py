
from os import stat_result
import sys
import inspect
import importlib
from pathlib import Path
from typing import Callable, List, Optional
import warnings

from pydantic import Field, validator
from redengine.core.parameters.arguments import BaseArgument

from redengine.core.task import Task
from redengine.core.parameters import Parameters
from redengine.pybox.pkg import find_package_root


def get_module(path, pkg_path=None):
    if pkg_path:
        name = '.'.join(
            path
            .with_suffix('') # path/to/file/myfile.py --> path.to.file.myfile
            .parts[len(pkg_path.parts):] # root/myproject/pkg/myfile.py --> myproject.pkg.myfile
        )
    else:
        name = Path(path).name

    spec = importlib.util.spec_from_file_location(name, path.absolute())
    task_module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(task_module)
    except Exception as exc:
        raise ImportError(f"Importing the file '{path}' failed.") from exc
    return task_module

def to_import_path(src:stat_result):
    imp = '.'.join(Path(src).with_suffix("").parts)
    return imp

class TempSysPath:
    # TODO: To utils.
    sys_path = sys.path
    def __init__(self, paths:list):
        self.paths = paths
    
    def __enter__(self):
        for path in self.paths:
            sys.path.append(path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for path in self.paths:
            try:
                self.sys_path.remove(path)
            except ValueError:
                pass

class FuncTask(Task):
    """Task that executes a function or callable.

    Parameters
    ----------
    func : Callable, str
        Function or name of a function to be executed. If string is
        passed, the path to the file where the function is should 
        be passed with ``path`` or in the argument, like
        "path/to/file.py:my_func".
    path : path-like
        Path to the function. Not needed if ``func`` is callable.
    delay : bool, optional
        If True, the function is imported and set to the task
        immediately. If False, the function is imported only 
        when running the task. By default False if ``func`` is 
        callable and True if ``func`` is a name of a function.
    sys_path : list of paths
        Paths that are appended to ``sys.path`` when the function
        is imported.
    **kwargs : dict
        See :py:class:`redengine.core.Task`


    Examples
    --------

    >>> from redengine.tasks import FuncTask
    >>> def myfunc():
    ...     ...
    >>> task = FuncTask(myfunc, name="my_func_task_1")

    **Via decorator:**

    >>> from redengine.tasks import FuncTask
    >>> @FuncTask(name='my_func_task_2', start_cond="daily")
    ... def myfunc():
    ...     ...

    If the ``name`` is not defined, the name will be in form
    ``path.to.module:myfunc``.

    Or from string using lazy importing:

    >>> from redengine.tasks import FuncTask
    >>> task = FuncTask("myfunc", path="path/to/script.py", name='my_func_task_3', start_cond="daily")

    Warnings
    --------

    If ``execution='process'``, only picklable functions can be used.
    The following will NOT work:

    .. code-block:: python

        # Lambda functions are not allowed
        FuncTask(lambda:None, execution="process")

    .. code-block:: python

        # nested functions are not allowed
        def my_func():
            @FuncTask(execution="process")
            def my_task_func():
                ...
        my_func()

    .. code-block:: python

        def my_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        # decorated functions are not allowed
        @my_decorator
        @FuncTask(execution="process")
        def my_task_func():
            ...
    """
    func: Optional[Callable] = Field(description="Executed function")

    path: Optional[Path] = Field(description="Path to the script that is executed")
    func_name: Optional[str] = Field(default="main", description="Name of the function in given path. Pass path as well")
    cache: bool = False

    sys_paths: List[Path] = []

    _delayed_kwargs: dict = {}
    _name_template: str = '{module_name}:{func_name}'
    @property
    def delayed(self):
        return self.func is None

    @validator('path')
    def validate_path(cls, value: Path, values):
        name = values['name']
        if value is not None and not value.is_file():
            warnings.warn(f"Path {value} does not exists. Task '{name}' may fail.")
        return value

    @validator("func")
    def validate_func(cls, value, values):
        execution = values.get('execution')
        func = value
    
        if execution == "process" and getattr(func, "__name__", None) == "<lambda>":
            raise AttributeError(
                f"Cannot pickle lambda function '{func}'. "
                "The function must be pickleable if task's execution is 'process'. "
            )
        return value

    def __init__(self, func=None, **kwargs):
        only_func_set = func is not None and not kwargs
        no_func_set = func is None and kwargs.get('path') is None
        if no_func_set:
            # FuncTask was probably called like:
            # @FuncTask(...)
            # def myfunc(...): ...

            # We initiate the class lazily by creating
            # almost empty shell class that is populated
            # in next __call__ (which should occur immediately)
            self._delayed_kwargs = kwargs
            return 
        elif only_func_set:
            # Most likely called as:
            # @FuncTask
            # def myfunc(...): ...
            
            # We are slightly forgiving and set 
            # the execution to else than process
            # as it's obvious it would not work.
            kwargs["execution"] = "thread"

        super().__init__(func=func, **kwargs)
        self._set_descr()

    def __call__(self, *args, **kwargs):
        if not hasattr(self, "func"):
            func = args[0]
            super().__init__(func=func, **self._delayed_kwargs)
            self._set_descr()
            self._delayed_kwargs = {}

            # Note that we must return the function or 
            # we are in deep shit with multiprocessing
            # (or pickling the function).
            return func
        else:
            return super().__call__(*args, **kwargs)

    def _set_descr(self):
        "Set description from func doc if desc missing"
        if self.description is None and hasattr(self.func, "__doc__"):
            self.description = self.func.__doc__

    def execute(self, **params):
        "Run the actual, given, task"
        func = self.get_func(cache=self.cache)
        output = func(**params)
        return output

    def get_func(self, cache=True):
        if self.func is None:
            # Add dir of self.path to sys.path so importing from that dir works
            pkg_path = find_package_root(self.path)
            root = str(Path(self.path).parent.absolute()) if not pkg_path else str(pkg_path)

            # _task_func is cached to faster performance
            with TempSysPath([root] + self.sys_paths):
                task_module = get_module(self.path, pkg_path=pkg_path)
            task_func = getattr(task_module, self.func_name)

            if cache:
                self.func = task_func
            return task_func
        else:
            return self.func

    def get_default_name(self, func=None, path=None, func_name=None, _name_template=None, **kwargs):
        if func is None:
            file = Path(path)
            module_name = '.'.join(file.parts).replace(".py", "")
        else:
            module_name = func.__module__
            func_name = getattr(func, "__name__", type(func).__name__)
            if module_name == "__main__":
                # Showing as 'myfunc'
                return func_name
        if _name_template is not None:
            return _name_template.format(module_name=module_name, func_name=func_name)
        else:
            return f'{module_name}:{func_name}'

    def process_finish(self, *args, **kwargs):
        if self.is_delayed():
            # Deleting the _func so it is refreshed
            # next time the task is run.
            self._func = None
        super().process_finish(*args, **kwargs)

    def is_delayed(self):
        return self.func is None
        
    def get_task_params(self):
        params = super().get_task_params()

        # Get params from the typehints
        cache = False if self.path is not None else True
        func = self.get_func(cache=cache)
        func_params = inspect.signature(func).parameters
        for name, param in func_params.items():
            default = param.default
            if isinstance(default, BaseArgument):
                params[name] = default.get_value(task=self)
        return params

    def prefilter_params(self, params):
        if not self.is_delayed():
            # Filter the parameters now so that 
            # we pass as little as possible to 
            # pickling. If lazy, we filter after
            # pickling to handle problems in 
            # pickling functions.
            return {
                key: val for key, val in params.items()
                if key in self.kw_args
            }
        else:
            return params

    def postfilter_params(self, params:Parameters):
        if self.is_delayed():
            # Was not filtered in prefiltering.
            return {
                key: val for key, val in params.items()
                if key in self.kw_args
            }
        else:
            return params

    @property
    def pos_args(self):
        func = self.get_func()
        sig = inspect.signature(func)
        pos_args = [
            val.name
            for name, val in sig.parameters.items()
            if val.kind in (
                inspect.Parameter.POSITIONAL_ONLY, # NOTE: Python <= 3.8 do not have positional arguments, but maybe in the future?
                inspect.Parameter.POSITIONAL_OR_KEYWORD # Keyword argument
            )
        ]
        return pos_args

    @property
    def kw_args(self):
        func = self.get_func()
        sig = inspect.signature(func)
        kw_args = [
            val.name
            for name, val in sig.parameters.items()
            if val.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD, # Normal argument
                inspect.Parameter.KEYWORD_ONLY # Keyword argument
            )
        ]
        return kw_args
