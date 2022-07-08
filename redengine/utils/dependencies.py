
from typing import TYPE_CHECKING, DefaultDict, List, Optional, Union

from pydantic import BaseModel
from redengine._base import RedBase
from redengine.conditions import Any, All, DependFinish, DependSuccess
from redengine.conditions.task import DependFailure
from redengine.core import Task
from redengine.core.condition.base import BaseCondition

from redengine import Session

class Link:

    def __init__(self, 
                 parent: Task, 
                 child: Task, 
                 relation: Optional[Union[DependSuccess, DependFailure, DependFinish]]=None, 
                 type: Optional[Union[Any, All]]=None):
        self.parent = parent
        self.child = child
        self.relation = relation
        self.type = type

    def __iter__(self):
        return iter((self.parent, self.child))

    def __eq__(self, other):
        if type(self) == type(other):
            return (
                self.parent == other.parent
                and self.child == other.child
                and self.relation == other.relation
                and self.type == other.type
            )
        else:
            return False

    def __str__(self):
        s = f'{self.parent.name!r} -> {self.child.name!r}'
        if self.type is All:
            s = s + ' (multi)'
        return s

    def __repr__(self):
        return f'Link({self.parent.name}, {self.child.name}, relation={getattr(self.relation, "__name__", None)}, type={getattr(self.type, "__name__", None)})'

class Dependencies(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    session: Session

    def __init__(self, session, **kwargs):
        super().__init__(session=session, **kwargs)

    def __iter__(self):
        for task in self.session.tasks:
            yield from self._get_links(task)

    def _get_links(self, task:Task) -> Union[Any, All]:
        cond = task.start_cond
        if isinstance(cond, (Any, All)):
            for subcond in cond:
                if isinstance(subcond, (DependFinish, DependSuccess, DependFailure)):
                    req_task = subcond.kwargs['depend_task']
                    req_task = self.session.get_task(req_task)
                    yield Link(parent=req_task, child=task, relation=type(subcond), type=type(cond))
        elif isinstance(cond, (DependFinish, DependSuccess, DependFailure)):
            req_task = cond.kwargs['depend_task']
            req_task = self.session.get_task(req_task)
            yield Link(req_task, task, relation=type(cond))


def get_dependencies(session) -> List[Link]:
    "Get list of dependency links"
    return list(Dependencies(session))