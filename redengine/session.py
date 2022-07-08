

"""
Utilities for getting information 
about the scehuler/task/parameters etc.
"""

import datetime
import logging
from multiprocessing import cpu_count
from pathlib import Path
import warnings
import pandas as pd

from pydantic import BaseModel, PrivateAttr, validator
from redengine.log.defaults import create_default_handler
from typing import TYPE_CHECKING, Callable, ClassVar, Iterable, Dict, List, Optional, Set, Tuple, Type, Union, Any
from itertools import chain

from redbird.logging import RepoHandler
from redengine._base import RedBase

if TYPE_CHECKING:
    from redengine.core.log import TaskAdapter
    from redengine.parse import StaticParser
    from redengine.core import (
        Task,
        Scheduler,
        BaseCondition,
        Parameters,
        BaseArgument,
        TimePeriod
    )

class Config(BaseModel):
    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True

    use_instance_naming: bool = False
    task_priority: int = 0
    task_execution: str = 'process'
    task_pre_exist: str = 'raise'
    force_status_from_logs: bool = False # Force to check status from logs every time (slow but robust)
    
    task_logger_basename: str = "redengine.task"
    scheduler_logger_basename: str = "redengine.scheduler"

    silence_task_prerun: bool = False # Whether to silence errors occurred in setting a task to run
    silence_cond_check: bool = False # Whether to silence errors occurred in checking conditions
    cycle_sleep: int = None
    debug: bool = False

    max_process_count = cpu_count()
    tasks_as_daemon: bool = True
    restarting: str = 'replace'
    instant_shutdown: bool = False

    timeout: datetime.timedelta = datetime.timedelta(minutes=30)
    shut_cond: Optional['BaseCondition'] = None

    @validator('shut_cond', pre=True)
    def parse_shut_cond(cls, value):
        from redengine.parse import parse_condition
        from redengine.conditions import AlwaysFalse
        if value is None:
            return AlwaysFalse()
        return parse_condition(value)

    @validator('timeout')
    def parse_timeout(cls, value):
        if isinstance(value, str):
            return pd.Timedelta(value).to_pytimedelta()
        elif isinstance(value, (float, int)):
            return datetime.timedelta(milliseconds=value * 1000)
        else:
            return value

class Hooks(BaseModel):
    task_init: List[Callable] = []
    task_execute: List[Callable] = []
    
    scheduler_startup: List[Callable] = []
    scheduler_cycle: List[Callable] = []
    scheduler_shutdown: List[Callable] = []

class Session(RedBase):
    """Collection of the scheduler objects.

    Parameters
    ----------

    config : dict, optional
        Central configuration for defining behaviour
        of different object and classes in the session.
    tasks : Dict[str, redengine.core.Task], optional
        Tasks of the session. Can be formed later.
    parameters : parameter-like, optional
        Session level parameters.
    scheme : str or list, optional
        Premade scheme(s) to use to set up logging, 
        parameters, setup tasks etc.
    as_default : bool, default=True
        Whether to set the session as default for next
        tasks etc. that don't have session
        specified.
    kwds_scheduler : dict, optional
        Keyword arguments passed to 
        :py:class:`redengine.core.Scheduler`.
    delete_existing_loggers : bool, default=False
        If True, deletes the loggers that already existed
        for the task logger basename.

    Attributes
    ----------
    config : dict
        Central configuration for defining behaviour
        of different object and classes in the session.
    scheduler : Scheduler
        Scheduler of the session.
    delete_existing_loggers : bool
        If True, all loggers that match the 
        session.config.basename are deleted (by 
        default, deletes loggers starting with 
        'redengine.task').

    """
    config: Config = Config()
    class Config:
        arbitrary_types_allowed = True

    tasks: Set['Task']
    hooks: Hooks
    parameters: 'Parameters'
    _scheduler: 'Scheduler'

    _time_parsers: ClassVar[Dict] = {}
    _cls_cond_parsers: ClassVar[Dict] = {} # Default condition parsers

    def _get_parameters(self, value):
        from redengine.core import Parameters
        if value is None:
            return Parameters()
        elif not isinstance(value, Parameters):
            value = Parameters(value)
        return value

    def _get_config(self, value):
        if value is None:
            return Config()
        elif isinstance(value, dict):
            return Config(**value)
        elif isinstance(value, Config):
            return value
        else:
            raise TypeError("Invalid config type")

    def __init__(self, config=None, parameters=None, delete_existing_loggers=False):
        from redengine.core import Scheduler
        self.config = self._get_config(config)
        self.parameters = self._get_parameters(parameters)
        self.scheduler = Scheduler(self)
        self.tasks = set()
        self.hooks = Hooks()
        self.returns = self._get_parameters(None)
        self._cond_parsers = self._cls_cond_parsers.copy()
        self._cond_cache: Dict = {} # Cached by CondParser to speed up expensive conditions
        self._cond_states = {} # Used by FuncConds to relay condiiton states to conditions
        if delete_existing_loggers:
            self.delete_task_loggers()

    def __getitem__(self, task:Union['Task', str]):
        "Get a task from the session"
        task_name = task.name if not isinstance(task, str) else task
        for task in self.tasks:
            if task.name == task_name:
                return task
        else:
            raise KeyError(f"Task '{task_name}' not found")

    def __contains__(self, task: Union['Task', str]):
        "Check if task is in session"
        try:
            self[task]
        except KeyError:
            return False
        else:
            return True

    def start(self):
        """Start the scheduling session.

        Will block and wait till the scheduler finishes 
        if there is a shut condition."""
        self._check_readable_logger()
        self.scheduler()

    def run(self, *task_names:Tuple[str], execution=None, obey_cond=False):
        """Run specific task(s) manually.

        This method starts up the scheduler but only the given
        task is run. Useful to manually run a task while using
        the setup/teardown and parameters of the session and 
        scheduler.

        Parameters
        ----------
        *task_names : tuple of str
            Names of the tasks to run.
        execution : str
            Execution method for all of the tasks.
            By default, whatever set to each task
        obey_cond : bool
            Whether to obey the ``start_cond`` or 
            force a run regardless. By default, False

        .. warning::

            This is not meant to be called by tasks or the system
            itself. Just to run specific tasks when the system itself
            is not running.
        """
        self._check_readable_logger()
        # To prevent circular import
        from redengine.conditions.scheduler import SchedulerCycles

        orig_vals = {}
        for task in self.tasks:
            name = task.name
            orig_vals[name] = {
                attr: val for attr, val in task.__dict__.items()
                if attr not in ("status", "last_run", "last_success", "last_fail", "last_terminate")
            }
            if name in task_names:
                if not obey_cond:
                    task.force_run = True
                if execution is not None:
                    task.execution = execution
            else:
                task.disabled = True
        
        orig_shut_cond = self.config.shut_cond
        try:
            self.config.shut_cond = SchedulerCycles() >= 1
            self.start()
        finally:
            self.config.shut_cond = orig_shut_cond
            # Set back the disabled, execution etc.
            for task in self.tasks:
                task.__dict__.update(orig_vals[task.name])

    def restart(self):
        """Restart the scheduler
        
        The restart is not instantenous and 
        will occur after the scheduler finishes
        checking one cycle of tasks."""
        self.scheduler._flag_restart.set()

    def shutdown(self):
        """Shut down the scheduler
        
        The shut down is not instantenous and 
        will occur after the scheduler finishes
        checking one cycle of tasks."""
        self.scheduler._flag_shutdown.set()

    def _check_readable_logger(self):
        from redengine.core.log import TaskAdapter
        task_logger_basename = self.config.task_logger_basename
        task_logger = logging.getLogger(task_logger_basename)
        logger = TaskAdapter(task_logger, None, ignore_warnings=True)
        if logger.is_readable_unset:
            # Setting memory logger 
            warnings.warn(
                f"Logger {task_logger_basename} cannot be read. " 
                "Logging is set to memory. " 
                "To supress this warning, "
                "please set a handler that can be read (redbird.logging.RepoHandler)", UserWarning)

            # Setting memory logger
            task_logger.addHandler(create_default_handler())
        is_info_logged = logger.getEffectiveLevel() <= logging.INFO
        if not is_info_logged:
            level_name = logging.getLevelName(task_logger.getEffectiveLevel())
            warnings.warn(
                f"Logger {task_logger_basename} has too low level ({level_name}). " 
                "Level is set to INFO to make sure the task logs get logged. ", UserWarning)
            task_logger.setLevel(logging.INFO)

    def get_tasks(self) -> list:
        """Get session tasks as list.

        Returns
        -------
        list[redengine.core.Task]
            List of tasks in the session.
        """
        return self.tasks

    def get_task(self, task):
        #! TODO: Do we need this?
        return self[task]

    def get_cond_parsers(self):
        "Used by the actual string condition parser"
        return self._cond_parsers

    def add_task(self, task: 'Task'):
        "Add the task to the session"
        if_exists = self.config.task_pre_exist
        exists = task in self
        if exists:
            if if_exists == 'ignore':
                return
            elif if_exists == 'replace':
                self.tasks.remove(task)
                self.tasks.add(task)
            elif if_exists == 'raise':
                raise KeyError(f"Task '{task.name}' already exists")
        else:
            self.tasks.add(task)

    def task_exists(self, task: 'Task'):
        task_name = task.name if not isinstance(task, str) else task
        for task in self.tasks:
            if task.name == task_name:
                return True
        else:
            return False

    def get_repo(self):
        "Get log repo where the task logs are stored"
        from redengine.core.log import TaskAdapter
        basename = self.config.task_logger_basename
        logger = logging.getLogger(basename)
        return TaskAdapter(logger, task=None)._get_repo()

    def get_task_loggers(self, with_adapters=True) -> Dict[str, Union['TaskAdapter', logging.Logger]]:
        """Get task logger(s) from the session.

        Parameters
        ----------
        with_adapters : bool, optional
            Whether get the loggers wrapped to 
            redengine.core.log.TaskAdapter, by default True

        Returns
        -------
        Dict[str, Union[TaskAdapter, logging.Logger]]
            Dictionary of the loggers (or adapters)
            in which the key is the logger name.
            Placeholders and loggers built for parallelized
            tasks are ignored.
        """
        from redengine.core.log import TaskAdapter

        basename = self.config.task_logger_basename
        return {
            # The adapter should not be used to log (but to read) thus task_name = None
            name: TaskAdapter(logger, None) if with_adapters else logger 
            for name, logger in logging.root.manager.loggerDict.items() 
            if name.startswith(basename) 
            and not isinstance(logger, logging.PlaceHolder)
            and not name.endswith("_process") # No private
        }

# Log data
    def get_task_log(self, *args, **kwargs) -> Iterable[Dict]:
        """Get task log records from all of the 
        readable handlers in the session.

        Parameters
        ----------
        **kwargs : dict
            Query parameters passed to 
            redengine.core.log.TaskAdapter.get_records

        Returns
        -------
        Iterable[Dict]
            Generator of the task log records.
        """
        loggers = self.get_task_loggers(with_adapters=True)
        data = iter(())
        for logger in loggers.values():
            data = chain(data, logger.get_records(*args, **kwargs))
        return data
        
    def delete_task_loggers(self):
        """Delete the previous loggers from task logger"""
        loggers = logging.Logger.manager.loggerDict
        for name in list(loggers):
            if name.startswith(self.config.task_logger_basename):
                del loggers[name]

    def clear(self):
        """Clear tasks, parameters etc. of the session"""
        #! TODO: Remove?
        from redengine.core import Parameters

        self.tasks = set()
        self.parameters = Parameters()

    def __getstate__(self):
        # NOTE: When a process task is executed, it will pickle
        # the task.session. Therefore removing unpicklable here.
        state = self.__dict__.copy()
        state["tasks"] = set()
        state["_cond_cache"] = None
        state["_cond_parsers"] = None
        state["session"] = None
        #state["parameters"] = None
        state['scheduler'] = None
        return state

    @property
    def env(self):
        "Shorthand for parameter 'env'"
        return self.parameters.get("env")

    @env.setter
    def env(self, value):
        "Shorthand for parameter 'env'"
        self.parameters["env"] = value

    def set_as_default(self):
        """Set this session as the default session for 
        next tasks, conditions and schedulers that
        are created.
        """

        RedBase.session = self

        import redengine
        redengine.session = self

    def hook_startup(self):
        def wrapper(func):
            self.hooks.scheduler_startup.append(func)
            return func
        return wrapper

    def hook_shutdown(self):
        def wrapper(func):
            self.hooks.scheduler_shutdown.append(func)
            return func
        return wrapper

    def hook_scheduler_cycle(self):
        def wrapper(func):
            self.hooks.scheduler_cycle.append(func)
            return func
        return wrapper

    def hook_task_init(self):
        def wrapper(func):
            self.hooks.task_init.append(func)
            return func
        return wrapper

    def hook_task_execute(self):
        def wrapper(func):
            self.hooks.task_execute.append(func)
            return func
        return wrapper
