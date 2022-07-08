
import re, time
import datetime

from redbird.oper import in_, between

from redengine.core.condition import All, Any, Statement


class DependMixin:

    _dep_actions = None

    def __init__(self, depend_task, task=None, **kwargs):
        super().__init__(task=task, depend_task=depend_task, **kwargs)

    @classmethod
    def _parse_multi_all(cls, depend_tasks:str, task=None):
        from redengine.parse import ParserError
        tasks = depend_tasks.split("', '")
        if not tasks:
            raise ParserError
        return All(*(cls(depend_task=dep_task, task=task) for dep_task in tasks))

    @classmethod
    def _parse_multi_any(cls, depend_tasks:str, task=None):
        from redengine.parse import ParserError
        tasks = depend_tasks.split("', '")
        if not tasks:
            raise ParserError
        return Any(*(cls(depend_task=dep_task, task=task) for dep_task in tasks))

    def observe(self, task, depend_task, **kwargs):
        """True when the "depend_task" has succeeded and "task" has not yet ran after it.
        Useful for start cond for task that should be run after success of another task.
        """
        actual_task = self.session.get_task(task)
        depend_task = self.session.get_task(depend_task)

        #! TODO: use Task._last_success & Task._last_run if not none and not forced
        last_depend_finish = depend_task.logger.get_latest(action=in_(self._dep_actions))
        last_actual_start = actual_task.logger.get_latest(action="run")

        if not last_depend_finish:
            # Depend has not run at all
            return False
        elif not last_actual_start:
            # Depend has succeeded but the actual task has not
            return True
            
        return self._get_field_value(last_depend_finish, "created") > self._get_field_value(last_actual_start, "created")

class TaskStatusMixin:

    _action = None

    def observe(self, task, _start_=None, _end_=None, **kwargs):

        task = Statement.session.get_task(task)
        if _start_ is None and _end_ is None:
            now = datetime.datetime.fromtimestamp(time.time())
            interv = task.period.rollback(now)
            _start_, _end_ = interv.left, interv.right
        
        allow_optimization = not self.session.config.force_status_from_logs

        if allow_optimization:
            
            # Get features that could be used to bypass reading logs
            if isinstance(self._action, str):
                last_occur = getattr(task, f'last_{self._action}')
                occurred_on_period = _start_ <= last_occur <= _end_ if last_occur is not None else False
                cannot_have_occurred = last_occur is None or last_occur < _start_
            else:
                # Multiple actions
                cannot_have_occurred = True
                for action in self._action:
                    last_occur = getattr(task, f'last_{action}')
                    if last_occur is not None and _start_ <= last_occur <= _end_:
                        occurred_on_period = True
                        cannot_have_occurred = False
                        break
                    elif last_occur is not None and last_occur >= _start_:
                        cannot_have_occurred = False
                else:
                    occurred_on_period = False
            
            # Check if can be determined without reading logs
            # NOTE: if the last_occurred > _end_, we cannot determine whether the cond is true or not
            if self.equal_zero():
                if cannot_have_occurred:
                    return True
                elif occurred_on_period:
                    return False
            elif self.any_over_zero():
                if cannot_have_occurred:
                    # If never occurred, it hasn't occurred on the period either
                    return False
                elif occurred_on_period:
                    return True

        
        records = task.logger.get_records(
            created=between(self._to_timestamp(_start_), self._to_timestamp(_end_)), 
            action=in_(self._action) if isinstance(self._action, list) else self._action
        )
        return [
            self._get_field_value(record, "created") 
            for record in records
        ]

    def __str__(self):
        if hasattr(self, "_str"):
            return self._str
        period = self.period
        task = self.kwargs["task"]
        return f"task 'task '{task}' {self._action} {period}"
