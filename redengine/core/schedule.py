
from multiprocessing import cpu_count
import multiprocessing
from typing import TYPE_CHECKING, Callable, Optional, Union
import threading
import time
import sys, os, subprocess
import logging
import datetime
import platform
from copy import copy
from queue import Empty

import pandas as pd

from redengine._base import RedBase
from redengine.core.condition import BaseCondition, AlwaysFalse
from redengine.core.task import Task
from redengine.exc import SchedulerRestart, SchedulerExit
from redengine.core.hook import _Hooker

if TYPE_CHECKING:
    from redengine import Session
class Scheduler(RedBase):
    """Multiprocessing scheduler

    Parameters
    ----------
    session : redengine.session.Session, optional
        Session object containing tasks,
        parameters and settings, 
        by default None
    max_processes : int, optional
        Maximum number of processes
        allowed to be started, 
        by default number of CPUs
    tasks_as_daemon : bool, optional
        Whether process tasks are run
        as daemon (if not specified in
        the task) or not, by default True
    timeout : str, optional
        Timeout of each task if not specified
        in the task itself. Must be timedelta
        string, by default "30 minutes"
    parameters : [type], optional
        Parameters of the session.
        Can also be passed directly to the 
        session, by default None
    logger : [type], optional
        [description], by default None
    name : str, optional
        Name of the scheduler, deprecated, by default None
    restarting : str, optional
        How the scheduler is restarted if 
        Restart exception is raised, by default 
        "replace"
    instant_shutdown : bool, optional
        Whether the scheduler tries to shut down
        as quickly as possible or wait till all
        the tasks have finished, by default False

    Attributes
    ----------
    session : redengine.session.Session
        Session for which the scheduler is
        for. One session has only one 
        scheduler.
    """
    session: 'Session'

    def __init__(self, session=None,
                logger=None, name:str=None):

        # Other
        self.session = session or self.session

        self.name = name if name is not None else id(self) #! TODO Is this needed?
        self.logger = logger


        # Controlling runtime (used by scheduler.disabled)
        self._flag_enabled = threading.Event()
        self._flag_shutdown = threading.Event()
        self._flag_restart = threading.Event()
        self._flag_enabled.set() # Not on hold by default

        # is_alive is used by testing whether the scheduler is 
        # still running or not
        self.is_alive = None

        self._log_queue = multiprocessing.Queue(-1)

    def _register_instance(self):
        self.session.scheduler = self

    @property
    def tasks(self):

        #! TODO: Is this needed?
        tasks = self.session.get_tasks()
        # There may be extra rare situation that priority is not in the task
        # for short period if it is being modified thus we use getattr
        return sorted(tasks, key=lambda task: getattr(task, "priority", 0), reverse=True)

    def __call__(self):
        """Start and run the scheduler. Will block till the end of the scheduling
        session."""
        # Unsetting some flags
        self._flag_shutdown.clear()
        self._flag_restart.clear()
        self._flag_enabled.set()

        self.is_alive = True
        exception = None
        try:
            self.startup()

            while not self.check_cond(self.session.config.shut_cond):
                if self._flag_shutdown.is_set():
                    break
                elif self._flag_restart.is_set():
                    raise SchedulerRestart()

                self._hibernate()
                self.run_cycle()

                # self.maintain()
        except SystemExit as exc:
            self.logger.info('Shutting down...', extra={"action": "shutdown"})
            exception = exc

        except SchedulerExit as exc:
            self.logger.info('Shutdown called. Shutting down...', exc_info=True, extra={"action": "shutdown"})
            exception = exc

        except SchedulerRestart as exc:
            self.logger.info('Restart called. Shutting down...', exc_info=True, extra={"action": "shutdown"})
            exception = exc

        except KeyboardInterrupt as exc:
            self.logger.info('Interupted. Shutting down...', exc_info=True, extra={"action": "shutdown"})
            exception = exc

        except Exception as exc:
            self.logger.critical('Fatal error encountered. Shutting down...', exc_info=True, extra={"action": "crash"})
            exception = exc
            raise
        else:
            self.logger.info('Purpose completed. Shutting down...', extra={"action": "shutdown"})
        finally:
            self.shut_down(exception=exception)

    def run_cycle(self):
        """Run one round of tasks.
        
        Each task is inspected and in case their starting condition
        is fulfilled, they are run.  A task can be running once at 
        any given time (in other words, multiple paraller execution 
        of a single task is not supported at the moment). Tasks that 
        are running but their termination condition is fulfilled are 
        terminated.
        """
        tasks = self.tasks
        self.logger.debug(f"Beginning cycle with {len(tasks)} tasks...", extra={"action": "run"})

        # Running hooks
        hooker = _Hooker(self.session.hooks.scheduler_cycle)
        hooker.prerun(self)

        for task in tasks:
            with task.lock:
                self.handle_logs()
                if task.on_startup or task.on_shutdown:
                    # Startup or shutdown tasks are not run in main sequence
                    pass
                elif self._flag_enabled.is_set() and self.is_task_runnable(task):
                    # Run the actual task
                    self.run_task(task)
                    # Reset force_run as a run has forced
                    task.force_run = False
                elif self.is_timeouted(task):
                    # Terminate the task
                    self.terminate_task(task, reason="timeout")
                elif self.is_out_of_condition(task):
                    # Terminate the task
                    self.terminate_task(task)

        # Running hooks
        hooker.postrun()
        
        self.n_cycles += 1

    def check_cond(self, cond: Union[BaseCondition, Task]) -> bool:
        try:
            return bool(cond)
        except:
            if not self.session.config.silence_cond_check:
                raise
            return False

    def run_task(self, task:Task, *args, **kwargs):
        """Run a given task"""
        start_time = datetime.datetime.fromtimestamp(time.time())

        try:
            task(log_queue=self._log_queue)
        except (SchedulerRestart, SchedulerExit) as exc:
            raise 
        except Exception as exc:
            if not self.session.config.silence_task_prerun:
                raise
        else:
            exception = None
            status = "success"

    def terminate_all(self, reason:str=None):
        """Terminate all running tasks."""
        for task in self.tasks:
            if task.is_alive():
                self.terminate_task(task, reason=reason)

    def terminate_task(self, task, reason=None):
        """Terminate a given task."""
        self.logger.debug(f"Terminating task '{task.name}'")
        is_threaded = hasattr(task, "_thread")
        is_multiprocessed = hasattr(task, "_process")
        if task.is_alive_as_thread():
            # We can only kindly ask the thread to...
            # get the fuck out please.
            task._thread_terminate.set()

        elif task.is_alive_as_process():
            task._process.terminate()
            # Waiting till the termination is finished. 
            # Otherwise may try to terminate it many times as the process is alive for a brief moment
            task._process.join() 
            task.log_termination(reason=reason)

            # Resetting attr force_termination
            task.force_termination = False
        else:
            # The process/thread probably just died after the check
            pass

    def is_timeouted(self, task):
        """Check if the task is timeouted."""
        #! TODO: Can this be put to the Task?
        if task.permanent_task:
            # Task is meant to be on all the time thus no reason to terminate due to timeout
            return False
        elif not hasattr(task, "_thread") and not hasattr(task, "_process"):
            # Task running on the main process
            # cannot be left running
            return False
        elif not task.is_alive():
            return False

        timeout = (
            task.timeout if task.timeout is not None
            else self.session.config.timeout
        )
        
        if timeout is None:
            return False
        run_duration = datetime.datetime.fromtimestamp(time.time()) - task.get_last_run()
        return run_duration > timeout

    def is_task_runnable(self, task:Task):
        """Inspect whether the task should be run."""
        #! TODO: Can this be put to the Task?
        execution = task.get_execution()
        if execution == "process":
            is_not_running = not task.is_alive()
            has_free_processors = self.has_free_processors()
            is_condition = self.check_cond(task)
            return is_not_running and has_free_processors and is_condition
        elif execution == "main":
            is_condition = self.check_cond(task)
            return is_condition
        elif execution == "thread":
            is_not_running = not task.is_alive()
            is_condition = self.check_cond(task)
            return is_not_running and is_condition
        else:
            raise NotImplementedError(task.execution)

    def is_out_of_condition(self, task:Task):
        """Inspect whether the task should be terminated."""
        #! TODO: Can this be put to the Task?
        if not task.is_alive():
            # NOTE:
            # Task running on the main process
            # cannot be left running
            return False

        elif task.force_termination:
            return True

        else:
            return self.check_cond(task.end_cond)
            
    def handle_logs(self):
        """Handle the status queue and carries the logging on their behalf."""
        # TODO: This could be maybe done in the tasks
        queue = self._log_queue
        while True:
            try:
                record = queue.get(block=False)
            except Empty:
                break
            else:
                self.logger.debug(f"Inserting record for '{record.task_name}' ({record.action})")
                task = self.session.get_task(record.task_name)
                if record.action == "fail":
                    # There is a caveat in logging 
                    # https://github.com/python/cpython/blame/fad6af2744c0b022568f7f4a8afc93fed056d4db/Lib/logging/handlers.py#L1383 
                    # https://bugs.python.org/issue34334

                    # The traceback/exception info is no longer in record.exc_info/record.exc_text 
                    # and it has been formatted to record.message/record.msg
                    # This means we have to rely that message really contains
                    # the full traceback

                    record.exc_info = record.exc_text
                    record.exc_text = record.exc_text
                    if record.exc_text is not None and record.exc_text not in record.message:
                        record.message = record.message + "\n" + record.message
                elif record.action == "success":
                    # Take the return value from the record and delete
                    # Note that record has attr __return__ only if task running as process
                    return_value = record.__return__
                    task._handle_return(return_value)
                    del record.__return__
                
                task.log_record(record)

    def _hibernate(self):
        """Go to sleep and wake up when next task can be executed."""
        delay = self.session.config.cycle_sleep
        if delay is not None:
            time.sleep(delay)

    def startup(self):
        """Start up the scheduler.
        
        Starting up includes setting up attributes and
        running tasks that have ``on_startup`` as ``True``."""
        #self.setup_listener()
        self.logger.info(f"Starting up...", extra={"action": "setup"})
        hooker = _Hooker(self.session.hooks.scheduler_startup)
        hooker.prerun(self)

        self.n_cycles = 0
        self.startup_time = datetime.datetime.fromtimestamp(time.time())

        self.logger.info(f"Beginning startup sequence...")
        for task in self.tasks:
            if task.on_startup:
                if isinstance(task.start_cond, AlwaysFalse) and not task.disabled: 
                    # Make sure the tasks run if start_cond not set
                    task.force_run = True

                if self.is_task_runnable(task):
                    self.run_task(task)

        hooker.postrun()
        self.logger.info(f"Setup complete.")

    def has_free_processors(self) -> bool:
        """Whether the Scheduler has free processors to
        allocate more tasks."""
        return self.n_alive <= self.session.config.max_process_count

    @property
    def n_alive(self) -> int:
        """Count of tasks that are alive."""
        return sum(task.is_alive() for task in self.tasks)
        
    def _shut_down_tasks(self, traceback=None, exception=None):
        non_fatal_excs = (SchedulerRestart,) # Exceptions that are allowed to have graceful exit
        wait_for_finish = not self.session.config.instant_shutdown and (exception is None or isinstance(exception, non_fatal_excs))
        if wait_for_finish:
            try:
                # Gracefully shut down (allow remaining tasks to finish)
                while self.n_alive:
                    #time.sleep(self.min_sleep)
                    self.handle_logs()
                    for task in self.tasks:
                        if task.permanent_task:
                            # Would never "finish" anyways
                            self.terminate_task(task)
                        elif self.is_timeouted(task):
                            # Terminate the task
                            self.terminate_task(task, reason="timeout")
                        elif self.is_out_of_condition(task):
                            # Terminate the task
                            self.terminate_task(task)
            except Exception as exc:
                # Fuck it, terminate all
                self._shut_down_tasks(exception=exc)
                return
            else:
                self.handle_logs()
        else:
            self.terminate_all(reason="shutdown")

    def wait_task_alive(self):
        """Wait till all, especially threading tasks, are finished."""
        while self.n_alive > 0:
            time.sleep(0.005)

    def shut_down(self, traceback=None, exception=None):
        """Shut down the scheduler.
        
        Shutting down includes running tasks that have 
        ``on_shutdown`` as ``True``, handling the 
        shutting down of already running tasks and 
        restarting the scheduler in case restart was
        called.
        
        If non fatal exception was raised and ``instant_shutdown``
        is ``False``, remaining running tasks are waited to finish.
        Else all the tasks are terminated. If ``instant_shutdown``
        is ``True``, the scheduler won't wait for the terminated 
        tasks to finish their termination.
        """
        
        self.logger.info(f"Beginning shutdown sequence...")
        hooker = _Hooker(self.session.hooks.scheduler_shutdown)
        hooker.prerun(self)

        # Make sure the tasks run if start_cond not set
        for task in self.tasks:
            if task.on_shutdown:

                if isinstance(task.start_cond, AlwaysFalse) and not task.disabled: 
                    # Make sure the tasks run if start_cond not set
                    task.force_run = True

                if self.is_task_runnable(task):
                    self.run_task(task)

        self.logger.info(f"Shutting down tasks...")
        self._shut_down_tasks(traceback, exception)

        if not self.session.config.instant_shutdown:
            self.wait_task_alive() # Wait till all tasks' threads and processes are dead

        # Running hooks
        hooker.postrun()

        self.is_alive = False
        self.logger.info(f"Shutdown completed. Good bye.")
        if isinstance(exception, SchedulerRestart):
            # Clean up finished, restart is finally
            # possible
            self._restart()

    def _restart(self):
        """Restart the scheduler by creating a new process
        on the temporary run script where the scheduler's is
        process is started.
        """
        # TODO
        # https://stackoverflow.com/a/35874988
        self.logger.debug(f"Restarting...", extra={"action": "restart"})
        python = sys.executable

        restarting = self.session.config.restarting
        if restarting == "replace":
            os.execl(python, python, *sys.argv)
            # After this, no code will be run. It all died :(
        elif restarting == "relaunch":
            # Relaunch the process
            subprocess.Popen([python, *sys.argv], shell=False, close_fds=True)
        elif restarting == "fresh":
            # Relaunch the process in new window
            if platform.system() == "Windows":
                subprocess.Popen([python, *sys.argv], shell=False, close_fds=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Linux does not have CREATE_NEW_CONSOLE creation flag but shell=True is pretty close
                subprocess.Popen([python, *sys.argv], shell=True, close_fds=True)
        elif restarting == "recall":
            # Mostly useful for testing.
            # Restart by calling the self.__call__ again 
            return self()
        else:
            raise ValueError(f"Invalid restaring: {restarting}")

# System control
    @property
    def on_hold(self):
        """bool: If True, the scheduler won't execute new tasks
        till this is set False. Useful to halt task execution in
        a controller task."""
        return not self._flag_enabled.is_set()

    @on_hold.setter
    def on_hold(self, value):
        if value:
            self._flag_enabled.clear()
        else:
            self._flag_enabled.set()

    def set_shut_down(self):
        """Shut down the scheduler. Useful to shut down the 
        scheduler in a controller task."""
        self.on_hold = False # In case was set to wait
        self._flag_shutdown.set()

# Logging
    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        basename = self.session.config.scheduler_logger_basename
        if logger is None:
            # Get class logger (default logger)
            logger = logging.getLogger(basename)

        if not logger.name.startswith(basename):
            raise ValueError(f"Logger name must start with '{basename}' as session finds loggers with names")

        # TODO: Use TaskAdapter to relay the scheduler name?
        self._logger = logger
