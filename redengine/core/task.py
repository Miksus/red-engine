
from pickle import PicklingError
import sys
import time
import datetime
import logging
import platform
from types import FunctionType, TracebackType
import warnings
from copy import copy
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, ClassVar, List, Dict, Literal, Type, Union, Tuple, Optional, get_type_hints
import multiprocessing
import threading
from queue import Empty

import pandas as pd
from pydantic import BaseModel, Field, PrivateAttr, validator

from redengine._base import RedBase
from redengine.core.condition import BaseCondition, AlwaysFalse, All, set_statement_defaults
from redengine.core.time import TimePeriod
from redengine.core.parameters import Parameters
from redengine.core.log import TaskAdapter
from redengine.core.utils import is_pickleable, filter_keyword_args, is_main_subprocess
from redengine.exc import SchedulerRestart, SchedulerExit, TaskInactionException, TaskTerminationException
from redengine.core.meta import _register
from redengine.core.hook import _Hooker
from redengine.log import QueueHandler

if TYPE_CHECKING:
    from redengine import Session
    from redengine.core.parameters import BaseArgument

_IS_WINDOWS = platform.system()

class Task(RedBase, BaseModel):
    """Base class for Tasks.

    A task can be a function, command or other procedure that 
    does a specific thing. A task can be parametrized by supplying
    session level parameters or parameters on task basis.
    

    Parameters
    ----------
    name : str, optional
        Name of the task. Ideally, all tasks
        should have unique name. If None, the
        return value of Task.get_default_name() 
        is used instead.
    description : str, optional
        Description of the task. This is purely
        for task documentation purpose.
    start_cond : BaseCondition, optional
        Condition that when True the task
        is to be started, by default AlwaysFalse()
    end_cond : BaseCondition, optional
        Condition that when True the task
        will be terminated. Only works for for 
        tasks with execution='process' or 'thread'
        if thread termination is implemented in 
        the task, by default AlwaysFalse()
    execution : str, {'main', 'thread', 'process'}, default='process'
        How the task is executed. Allowed values
        'main' (run on main thread & process), 
        'thread' (run on another thread) and 
        'process' (run on another process).
    parameters : Parameters, optional
        Parameters set specifically to the task, 
        by default None
    disabled : bool
        If True, the task is not allowed to be run
        regardless of the start_cond,
        by default False
    force_run : bool
        If True, the task will be run once 
        regardless of the start_cond,
        by default True
    on_startup : bool
        Run the task on the startup sequence of 
        the Scheduler, by default False
    on_shutdown : bool
        Run the task on the shutdown sequence of 
        the Scheduler, by default False
    priority : int, optional
        Priority of the task. Higher priority
        tasks are first inspected whether they
        can be executed. Can be any numeric value.
        Setup tasks are recommended to have priority
        >= 40 if they require loaded tasks,
        >= 50 if they require loaded extensions.
        By default 0
    timeout : str, int, pd.Timedelta, optional
        If the task has not run in given timeout
        the task will be terminated. Only applicable
        for tasks with execution='process' or 
        with execution='thread'. Passed to 
        ``pandas.Timedelta``.
    daemon : Bool, optional
        Whether run the task as daemon process
        or not. Only applicable for execution='process',
        by default use Scheduler default
    on_exists : str
        What to do if the name of the task already 
        exists in the session, options: 'raise',
        'ignore', 'replace', by default use session
        configuration
    logger : str, logger.Logger, optional
        Logger of the task. Typically not needed
        to be set.
    session : redengine.session.Session, optional
        Session the task is binded to, 
        by default default session 


    Attributes
    ----------
    session : redengine.session.Session
        Session the task is binded to.
    logger : TaskAdapter
        Logger of the task. Access the 
        log records using task.logger.get_records()


    Examples
    --------
    Minimum example:

    >>> from redengine.core import Task
    >>> class MyTask(Task):
    ...     def execute(self):
    ...         ... # What the task does.
    ...         return ...

    """
    class Config:
        arbitrary_types_allowed= True
        underscore_attrs_are_private = True
        validate_assignment = True
        json_encoders = {
            Parameters: lambda v: dict(**v),
            'BaseCondition': lambda v: str(v),
            FunctionType: lambda v: v.__name__,
            'Session': lambda v: id(v),
        }


    session: 'Session' = Field()

    # Class
    permanent_task: bool = False # Whether the task is not meant to finish (Ie. RestAPI)
    _actions: ClassVar[Tuple] = ("run", "fail", "success", "inaction", "terminate", None, "crash_release")
    fmt_log_message: str = r"Task '{task}' status: '{action}'"

    daemon: Optional[bool]

    # Instance
    name: Optional[str] = Field(description="Name of the task. Must be unique")
    description: Optional[str] = Field(description="Description of the task for documentation")
    logger_name: Optional[str] = Field(description="Logger name to be used in logging the task records")
    execution: Optional[Literal['main', 'thread', 'process']]
    priority: int = 0
    disabled: bool = False
    force_run: bool = False
    force_termination: bool = False
    status: Optional[Literal['run', 'fail', 'success', 'terminate', 'inaction']] = Field(description="Latest status of the task")
    timeout: Optional[pd.Timedelta]

    parameters: Parameters = Parameters()

    start_cond: BaseCondition = AlwaysFalse() #! TODO: Create get_start_cond so that this could also be as string (lazily parsed)
    end_cond: BaseCondition = AlwaysFalse()

    on_startup: bool = False
    on_shutdown: bool = False

    last_run: Optional[datetime.datetime]
    last_success: Optional[datetime.datetime]
    last_fail: Optional[datetime.datetime]
    last_terminate: Optional[datetime.datetime]
    last_inaction: Optional[datetime.datetime]

    _process: multiprocessing.Process = None
    _thread: threading.Thread = None
    _thread_terminate: threading.Event = PrivateAttr(default_factory=threading.Event)
    _lock: Optional[threading.Lock] = PrivateAttr(default_factory=threading.Lock)

    _mark_running = False

    @validator('start_cond', pre=True)
    def parse_start_cond(cls, value, values):
        from redengine.parse.condition import parse_condition
        session = values['session']
        if isinstance(value, str):
            value = parse_condition(value, session=session)
        return copy(value)

    @validator('end_cond', pre=True)
    def parse_end_cond(cls, value, values):
        from redengine.parse.condition import parse_condition
        session = values['session']
        if isinstance(value, str):
            value = parse_condition(value, session=session)
        return copy(value)

    @validator('logger_name', pre=True, always=True)
    def parse_logger_name(cls, value, values):
        session = values['session']

        if isinstance(value, str):
            logger_name = value
        elif value is None:
            logger_name = session.config.task_logger_basename
        else:
            logger_name = value.name
            basename = session.config.task_logger_basename
            if not value.name.startswith(basename):
                raise ValueError(f"Logger name must start with '{basename}' as session finds loggers with names")
        return logger_name

    @validator('timeout', pre=True, always=True)
    def parse_timeout(cls, value, values):
        if value == "never":
            return pd.Timedelta.max.to_pytimedelta()
        elif value is not None:
            return pd.Timedelta(value).to_pytimedelta()
        else:
            return value

    @property
    def logger(self):
        logger = logging.getLogger(self.logger_name)
        return TaskAdapter(logger, task=self)

    def __init__(self, **kwargs):

        hooker = _Hooker(self.session.hooks.task_init)
        hooker.prerun(self)

        if kwargs.get("session") is None:
            kwargs['session'] = self.session
        kwargs['name'] = self._get_name(**kwargs)

        super().__init__(**kwargs)

        # Set default readable logger if missing 
        self.session._check_readable_logger()

        self._set_default_task()

        self.register()
        
        # Hooks
        hooker.postrun()

    def _get_name(self, name=None, **kwargs):
        if name is None:
            use_instance_naming = self.session.config.use_instance_naming
            if use_instance_naming:
                return id(self)
            else:
                return self.get_default_name(**kwargs)
        else:
            return name

    @validator('name', pre=True)
    def parse_name(cls, value, values):
        session = values['session']
        on_exists = session.config.task_pre_exist
        name_exists = value in session
        if name_exists:
            if on_exists == 'ignore':
                return value
            elif on_exists == 'raise':
                raise ValueError(f"Task name '{value}' already exists.")
            elif on_exists == 'rename':
                basename = value
                name = value
                num = 0
                while name in session:
                    num += 1
                    name = f"{basename} - {num}"
                return name
        return value

    @validator('name', pre=False)
    def validate_name(cls, value, values):
        session = values['session']
        on_exists = session.config.task_pre_exist
        name_exists = value in session

        if name_exists:
            if on_exists == 'ignore':
                return value
            raise ValueError(f"Task name '{value}' already exists. Please pick another")
        return value

    @validator('parameters', pre=True)
    def parse_parameters(cls, value):
        if isinstance(value, Parameters):
            return value
        else:
            return Parameters(value)

    def _set_default_task(self):
        "Set the task in subconditions that are missing "
        set_statement_defaults(self.start_cond, task=self)
        set_statement_defaults(self.end_cond, task=self)

    def __hash__(self):
        return id(self)

    def __call__(self, params:Union[dict, Parameters]=None, **kwargs):
        """Execute the task. Creates a new process
        (if execution='process'), a new thread
        (if execution='thread') or blocks and 
        runs till the task is completed (if 
        execution='main').

        Parameters
        ----------
        params : dict, Parameters, optional
            Extra parameters for the task. Also
            the session parameters, task parameters
            and extra parameters are acquired, by default None
        """

        # Remove old threads/processes
        # (using _process and _threads are most robust way to check if running as process or thread)
        if self._process is not None:
            self._process = None
        if self._thread:
            self._thread = None

        # The parameters are handled in the following way:
        #   - First extra parameters are fetched. This includes:
        #       - session.parameters
        #       - _task_, _session_, _thread_terminate_
        #   - Then these extras are prefiltered (called params)
        #   - Then the task parameters are fetched (direct_params)
        #   - If process/thread, these parameters are pre_materialized
        #   - Then the params are post filtered
        #   - Then params and direct_params are fed to the execute method
        execution = self.get_execution()
        try:
            params = self.get_extra_params(params)
            # Run the actual task
            if execution == "main":
                direct_params = self.parameters
                self._run_as_main(params=params, direct_params=direct_params, execution="main", **kwargs)
                if _IS_WINDOWS:
                    #! TODO: This probably is now solved
                    # There is an annoying bug (?) in Windows:
                    # https://bugs.python.org/issue44831
                    # If one checks whether the task has succeeded/failed
                    # already the log might show that the task finished 
                    # 1 microsecond in the future if memory logging is used. 
                    # Therefore we sleep that so condition checks especially 
                    # in tests will succeed. 
                    time.sleep(1e-6)
            elif execution == "process":
                self.run_as_process(params=params, **kwargs)
            elif execution == "thread":
                self.run_as_thread(params=params, **kwargs)
        except (SchedulerRestart, SchedulerExit):
            raise
        except Exception as exc:
            # Something went wrong in the initiation
            # and it did not reach to log_running
            self.log_running()
            self.log_failure()
            raise

    def __bool__(self):
        """Check whether the task can be run or not.
        
        If force_run is True, the task can be run regardless.
        If disabled is True, the task is prevented to be run 
        (unless force_true=True). 
        If neither of the previous, the start_cond is inspected
        and if it is True, the task can be run.
        """
        # Also add methods: 
        #    set_pending() : Set forced_state to False
        #    resume() : Reset forced_state to None
        #    set_running() : Set forced_state to True

        if self.force_run:
            return True
        elif self.disabled:
            return False

        cond = bool(self.start_cond)

        return cond

    def run_as_main(self, params:Parameters):
        return self._run_as_main(params, self.parameters)

    def _run_as_main(self, params:Parameters, direct_params:Parameters, execution=None, **kwargs):
        """Run the task on the current thread and process"""
        #self.logger.info(f'Running {self.name}', extra={"action": "run"})

        #old_cwd = os.getcwd()
        #if cwd is not None:
        #    os.chdir(cwd)

        # (If SystemExit is raised, it won't be catched in except Exception)
        if execution == "process":
            hooks = kwargs.get('hooks', [])
        else:
            hooks = self.session.hooks.task_execute
        hooker = _Hooker(hooks)
        hooker.prerun(self)

        status = None
        output = None
        exc_info = (None, None, None)
        params = self.postfilter_params(params)
        params = Parameters(params) | Parameters(direct_params)
        params = params.materialize(task=self)

        if execution == 'main':
            self.log_running()
        try:
            output = self.execute(**params)

            # NOTE: we process success here in case the process_success
            # fails (therefore task fails)
            self.process_success(output)
        except (SchedulerRestart, SchedulerExit):
            # SchedulerRestart is considered as successful task
            self.log_success()
            status = "succeeded"
            self.process_success(None)
            exc_info = sys.exc_info()
            # Note that these are never silenced
            raise

        except TaskInactionException:
            # Task did not fail, it did not succeed:
            #   The task started but quickly determined was not needed to be run
            #   and therefore the purpose of the task was not executed.
            self.log_inaction()
            status = "inaction"
            exc_info = sys.exc_info()
            
        except TaskTerminationException:
            # Task was terminated and the task's function
            # did listen to that.
            self.log_termination()
            status = "termination"
            exc_info = sys.exc_info()

        except Exception as exception:
            # All the other exceptions (failures)
            try:
                self.process_failure(*sys.exc_info())
            except:
                # Failure of failure processing
                self.log_failure()
            else:
                self.log_failure()
            status = "failed"
            #self.logger.error(f'Task {self.name} failed', exc_info=True, extra={"action": "fail"})

            exc_info = sys.exc_info()
            if execution is None:
                raise

        else:
            # Store the output
            if execution != 'process':
                self._handle_return(output)
            self.log_success(output)
            #self.logger.info(f'Task {self.name} succeeded', extra={"action": "success"})
            status = "succeeded"
            
            return output

        finally:
            self.process_finish(status=status)
            self.force_run = False
            #if cwd is not None:
            #    os.chdir(old_cwd)
            hooker.postrun(*exc_info)

    def run_as_thread(self, params:Parameters, **kwargs):
        """Create a new thread and run the task on that."""

        params = params.pre_materialize(task=self)
        direct_params = self.parameters.pre_materialize(task=self)

        self._thread_terminate.clear()

        event_is_running = threading.Event()
        self._thread = threading.Thread(target=self._run_as_thread, args=(params, direct_params, event_is_running))
        self.last_run = datetime.datetime.fromtimestamp(time.time()) # Needed for termination
        self._thread.start()
        event_is_running.wait() # Wait until the task is confirmed to run 
 
    def _run_as_thread(self, params:Parameters, direct_params:Parameters, event=None):
        """Running the task in a new thread. This method should only
        be run by the new thread."""

        self.log_running()
        event.set()
        try:
            output = self._run_as_main(params=params, direct_params=direct_params, execution="thread")
        except:
            # Task crashed before actually running the execute.
            self.log_failure()
            # We cannot rely the exception to main thread here
            # thus we supress to prevent unnecessary warnings.

    def run_as_process(self, params:Parameters, daemon=None, log_queue: multiprocessing.Queue=None):
        """Create a new process and run the task on that."""

        params = params.pre_materialize(task=self)
        direct_params = self.parameters.pre_materialize(task=self)

        # Daemon resolution: task.daemon >> scheduler.tasks_as_daemon
        log_queue = self.session.scheduler._log_queue if log_queue is None else log_queue

        daemon = self.daemon if self.daemon is not None else self.session.config.tasks_as_daemon
        self._process = multiprocessing.Process(
            target=self._run_as_process, 
            args=(params, direct_params, log_queue, self.session.config, self._get_hooks("task_execute")), 
            daemon=daemon
        ) 
        #self._last_run = datetime.datetime.fromtimestamp(time.time()) # Needed for termination
        self._mark_running = True # needed in pickling
        
        self._process.start()
        self._mark_running = False
        
        self._lock_to_run_log(log_queue)
        return log_queue

    def _run_as_process(self, params:Parameters, direct_params:Parameters, queue, config, exec_hooks):
        """Running the task in a new process. This method should only
        be run by the new process."""

        # NOTE: This is in the process and other info in the application
        # cannot be accessed here. Self is a copy of the original
        # and cannot affect main processes' attributes!
        
        # The task's logger has been removed by MultiScheduler.run_task_as_process
        # (see the method for more info) and we need to recreate the logger now
        # in the actual multiprocessing's process. We only add QueueHandler to the
        # logger (with multiprocessing.Queue as queue) so that all the logging
        # records end up in the main process to be logged properly. 

        basename = self.logger_name
        # handler = logging.handlers.QueueHandler(queue)
        handler = QueueHandler(queue)

        # Set the process logger
        logger = logging.getLogger(basename + "._process")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.handlers = []
        logger.addHandler(handler)
        try:
            self.logger_name = logger.name
        except:
            logger.critical(f"Task '{self.name}' crashed in setting up logger.", exc_info=True, extra={"action": "fail", "task_name": self.name})
            raise
        self.log_running()
        try:
            # NOTE: The parameters are "materialized" 
            # here in the actual process that runs the task
            output = self._run_as_main(params=params, direct_params=direct_params, execution="process", hooks=exec_hooks)
        except Exception as exc:
            # Task crashed before running execute (silence=True)
            self.log_failure()

            # There is nothing to raise it
            # to :(
            pass

    def get_extra_params(self, params:Parameters) -> Parameters:
        """Get additional parameters from
        the session and extra for meta tasks
        including the task itself, session 
        and the thread terminate event.
        These parameters may or may not be used
        by the task.

        Included parameters:

        - _session_ : task's session
        - _task_ : the task itself
        - _thread_terminate_ : Task termination event if threading used (threading.Event)

        Returns
        -------
        Parameters
            Additional parameters
        """
        passed_params = Parameters(params)
        session_params = self.session.parameters
        task_params = Parameters(self.get_task_params())
        extra_params = Parameters(_session_=self.session, _task_=self, _thread_terminate_=self._thread_terminate)

        params = Parameters(self.prefilter_params(session_params | passed_params | extra_params))

        return params

    def get_task_params(self):
        "Get parameters passed to the task"
        return self.parameters

    def prefilter_params(self, params:Parameters):
        """Pre filter the parameters.
        
        This method filters the task parameters before 
        a thread or a process is created. This method 
        always called in the main process and in the 
        main thread. Therefore, one can filter here the 
        parameters that are problematic to pass to a 
        thread or process. 

        Parameters
        ----------
        params : redengine.core.Parameters

        Returns
        -------
        Parameters : dict, redengine.core.Parameters
            Filtered parameters.
        """
        return filter_keyword_args(self.execute, params)

    def postfilter_params(self, params:Parameters):
        """Post filter the parameters.
        
        This method filters the task parameters after 
        a thread or a process is created. This method 
        called in the child process, if ``execution='process'``, 
        or in the child thread ``execution='thread'``.
        For ``execution='main'``, overriding this method
        does not have much impact over overriding 
        ``prefilter_params``.

        Parameters
        ----------
        params : redengine.core.Parameters

        Returns
        -------
        Parameters : dict, redengine.core.Parameters
            Filtered parameters.
        """
        return params

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Run the actual task. Override this.
        
        Parameters are materialized to keyword arguments.
        """
        raise NotImplementedError(f"Method 'execute' not implemented to {type(self)}.")

    def process_failure(self, exc_type:Type[Exception], exc_val:Exception, exc_tb:TracebackType):
        """This method is executed after a failure of the task. 
        Override if needed.
        
        Parameters
        ----------
        exc_type : subclass of Exception
            Type of the occurred exception that caused the failure.
        exc_val : Exception
            Exception that caused the failure. 
        exc_type : Traceback object
            Traceback of the failure exception.
        """
        pass
    
    def process_success(self, output:Any):
        """This method is executed after a success of the task. 
        Override if needed.
        
        Parameters
        ----------
        output : Any
            Return value of the task.
        """
        pass

    def process_finish(self, status:str):
        """This method is executed after finishing the task. 
        Override if needed.
        
        Parameters
        ----------
        status : str {'succeeded', 'failed', 'termination', 'inaction'}
            How the task finished.
        """
        pass

    @property
    def is_running(self):
        """bool: Whether the task is currently running or not."""
        return self.get_status() == "run"

    def register(self):
        if hasattr(self, "_mark_register") and not self._mark_register:
            del self._mark_register
            return # on_exists = 'ignore'
        name = self.name
        self.session.add_task(self)

    def get_default_name(self, **kwargs):
        """Create a name for the task when name was not passed to initiation of
        the task. Override this method."""
        raise NotImplementedError(f"Method 'get_default_name' not implemented to {type(self)}")

    def is_alive(self) -> bool:
        """Whether the task is alive: check if the task has a live process or thread."""
        return self.is_alive_as_thread() or self.is_alive_as_process()

    def is_alive_as_thread(self) -> bool:
        """Whether the task has a live thread."""
        return self._thread is not None and self._thread.is_alive()

    def is_alive_as_process(self) -> bool:
        """Whether the task has a live process."""
        return self._process is not None and self._process.is_alive()
        
# Logging
    def _lock_to_run_log(self, log_queue):
        "Handle next run log to make sure the task started running before continuing (otherwise may cause accidential multiple launches)"
        action = None
        timeout = 10 # Seconds allowed the setup to take before declaring setup to crash
        #record = log_queue.get(block=True, timeout=None)
        while action != "run":
            try:
                record = log_queue.get(block=True, timeout=timeout)
            except Empty:
                if not self.is_alive():
                    # There will be no "run" log record thus ending the task gracefully
                    self.logger.critical(f"Task '{self.name}' crashed in setup", extra={"action": "fail"})
                    return
            else:
                
                #self.logger.debug(f"Inserting record for '{record.task_name}' ({record.action})")
                task = self.session.get_task(record.task_name)
                task.log_record(record)

                action = record.action

    def log_running(self):
        """Make a log that the task is currently running."""
        self._set_status("run")

    def log_failure(self):
        """Log that the task failed."""
        self._set_status("fail")

    def log_success(self, return_value=None):
        """Make a log that the task succeeded."""
        self._set_status("success", return_value=return_value)
        #self.status = "success"

    def log_termination(self, reason=None):
        """Make a log that the task was terminated."""
        reason = reason or "unknown reason"
        self._set_status("terminate", message=reason)

        # Reset event and force_termination (for threads)
        self._thread_terminate.clear()
        self.force_termination = False

    def log_inaction(self):
        """Make a log that the task did nothing."""
        self._set_status("inaction")

    def log_record(self, record:logging.LogRecord):
        """Log the record with the logger of the task.
        Also sets the status according to the record.
        """
        # Set last_run/last_success/last_fail etc.
        cache_attr = f"last_{record.action}"
        record_time = datetime.datetime.fromtimestamp(record.created)
        setattr(self, cache_attr, record_time)

        self.logger.handle(record)
        self.status = record.action

    def get_status(self) -> Literal['run', 'fail', 'success', 'terminate', 'inaction', None]:
        """Get latest status of the task."""
        if self.session.config.force_status_from_logs:
            try:
                record = self.logger.get_latest()
            except AttributeError:
                if is_main_subprocess():
                    warnings.warn(f"Task '{self.name}' logger is not readable. Status unknown.")
                record = None
            if not record:
                # No previous status
                return None
            status = record["action"] if isinstance(record, dict) else record.action
            self.status = status
            return status
        else:
            # This is way faster
            return self.status

    def _set_status(self, action, message=None, return_value=None):
        if message is None:
            message = self.fmt_log_message.format(action=action, task=self.name)

        if action not in self._actions:
            raise KeyError(f"Invalid action: {action}")
        
        if action is not None:
            now = datetime.datetime.fromtimestamp(time.time())
            if action == "run":
                extra = {"action": "run", "start": now}
                # self._last_run = now
            else:
                start_time = self.get_last_run()
                runtime = now - start_time if start_time is not None else None
                extra = {"action": action, "start": start_time, "end": now, "runtime": runtime}
            
            is_running_as_child = self.logger.name.endswith("._process")
            if is_running_as_child and action == "success":
                # If child process, the return value is passed via QueueHandler to the main process
                # and it's handled then in Scheduler.
                # Else the return value is handled in Task itself (__call__ & _run_as_thread)
                extra["__return__"] = return_value

            log_method = self.logger.exception if action == "fail" else self.logger.info
            log_method(
                message, 
                extra=extra
            )
            cache_attr = f"last_{action}"
            setattr(self, cache_attr, now)
        self.status = action

    def get_last_success(self) -> datetime.datetime:
        """Get the lastest timestamp when the task succeeded."""
        return self._get_last_action("success")

    def get_last_fail(self) -> datetime.datetime:
        """Get the lastest timestamp when the task failed."""
        return self._get_last_action("fail")

    def get_last_run(self) -> datetime.datetime:
        """Get the lastest timestamp when the task ran."""
        return self._get_last_action("run")

    def get_last_terminate(self) -> datetime.datetime:
        """Get the lastest timestamp when the task terminated."""
        return self._get_last_action("terminate")

    def get_last_inaction(self) -> datetime.datetime:
        """Get the lastest timestamp when the task inacted."""
        return self._get_last_action("inaction")

    def get_execution(self) -> str:
        if self.execution is None:
            return self.session.config.task_execution
        return self.execution

    def _get_last_action(self, action:str) -> datetime.datetime:
        cache_attr = f"last_{action}"

        if self.session is None:
            allow_cache = True
        else:
            allow_cache = not self.session.config.force_status_from_logs
        if allow_cache: #  and getattr(self, cache_attr) is not None
            value = getattr(self, cache_attr)
        else:
            value = self._get_last_action_from_log(action)
            if isinstance(value, float):
                value = datetime.datetime.fromtimestamp(value)
            setattr(self, cache_attr, value)
        return value

    def _get_last_action_from_log(self, action):
        """Get last action timestamp from log"""
        try:
            record = self.logger.get_latest(action=action)
        except AttributeError:
            if is_main_subprocess():
                warnings.warn(f"Task '{self.name}' logger is not readable. Latest {action} unknown.")
            return None
        else:
            if not record:
                return None
            timestamp = record["created"] if isinstance(record, dict) else record.created
            return timestamp

    def __getstate__(self):

        # # capture what is normally pickled
        # state = self.__dict__.copy()
        # 
        # # remove unpicklable
        # # TODO: Include conditions by enforcing tasks are passed to the conditions as names
        # state['_logger'] = None
        # state['_start_cond'] = None
        # state['_end_cond'] = None
        # #state["_process"] = None # If If execution == "process"
        # #state["_thread"] = None # If execution == "thread"
        # 
        # state["_thread_terminate"] = None # Event only for threads
        # 
        # state["_lock"] = None # Process task cannot lock anything anyways

        # capture what is normally pickled
        state = super().__getstate__()
        #state['__dict__'] = state['__dict__'].copy()

        # remove unpicklable
        state['__private_attribute_values__'] = state['__private_attribute_values__'].copy()
        priv_attrs = state['__private_attribute_values__']
        priv_attrs['_lock'] = None
        priv_attrs['_process'] = None
        priv_attrs['_thread'] = None
        priv_attrs['_thread_terminate'] = None

        # We also get rid of the conditions as if there is a task
        # containing an attr that cannot be pickled (like FuncTask
        # containing lambda function but ran as main/thread), we 
        # would face sudden crash.
        state['__dict__'] = state['__dict__'].copy()
        dict_state = state['__dict__']
        dict_state['start_cond'] = None
        dict_state['end_cond'] = None

        # Removing possibly unpicklable manually. There is a problem in Pydantic
        # and for some reason it does not use Session's pickling
        dict_state['parameters'] = Parameters()
        dict_state['session'] = None

        if not is_pickleable(state):
            if self._mark_running:
                # When this block might get executed?
                #   - If FuncTask func is non-picklable
                #       - There is another func with same name in the file
                #       - The function is lambda or decorated func
                unpicklable = {key: val for key, val in state.items() if not is_pickleable(val)}
                self.log_running()
                self.logger.critical(f"Task '{self.name}' crashed in pickling. Cannot pickle: {unpicklable}", extra={"action": "fail", "task_name": self.name})
                raise PicklingError(f"Task {self.name} could not be pickled. Cannot pickle: {unpicklable}")
            else:
                # Is pickled by something else than task execution
                return state

        # what we return here will be stored in the pickle
        return state

    def _handle_return(self, value):
        "Handle the return value (ie. store to parameters)"
        self.session.returns[self] = value

    def delete(self):
        """Delete the task from the session. 
        Overried if needed additional cleaning."""
        self.session.tasks.remove(self)

    def _get_hooks(self, name:str):
        return getattr(self.session.hooks, name)

# Other
    @property
    def period(self) -> TimePeriod:
        """TimePeriod: Time period in which the task runs

        Note that this should not be considered as absolute truth but
        as a best estimate.
        """
        from redengine.core.time import StaticInterval, All as AllTime
        from redengine.conditions import TaskFinished, TaskSucceeded

        cond = self.start_cond
        session = self.session

        if isinstance(cond, (TaskSucceeded, TaskFinished)):
            if session.get_task(cond.kwargs["task"]) is self:
                return cond.period

        elif isinstance(cond, All):
            task_periods = []
            for sub_stmt in cond:
                if isinstance(sub_stmt, (TaskFinished, TaskFinished)) and session.get_task(sub_stmt.kwargs["task"]) is self:
                    task_periods.append(sub_stmt.period)
            if task_periods:
                return AllTime(*task_periods)
        
        # TimePeriod could not be determined
        return StaticInterval()

    @property
    def lock(self):
        # Lock is private in a sense that we want to hide it from 
        # the model (if put to dict etc.) but public in a sense
        # that the user should be allowed to interact with it
        return self._lock

    def json(self, **kwargs):
        if 'exclude' not in kwargs:
            kwargs['exclude'] = set()
        kwargs['exclude'].update({'session'})
        return super().json(**kwargs)
