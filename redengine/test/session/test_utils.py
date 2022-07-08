
import pytest
from textwrap import dedent

from redengine.conditions.task import DependFailure, DependFinish, DependSuccess
from redengine.core.condition.base import All, Any
from redengine.tasks import FuncTask
from redengine import Session
from redengine.utils.dependencies import Dependencies, Link

def test_dependency(session):
    ta = FuncTask(lambda: None, name="a", start_cond="daily", execution="main")
    tb = FuncTask(lambda: None, name="b", start_cond="after task 'a'", execution="main")
    tc = FuncTask(lambda: None, name="c", start_cond="after task 'a' & after task 'b' failed", execution="main")
    td = FuncTask(lambda: None, name="d", start_cond="after task 'a' | after task 'b'", execution="main")

    te = FuncTask(lambda: None, name="no link", start_cond="daily", execution="main")

    deps = Dependencies(session)
    deps_list = sorted(deps, key=lambda x: (x.child.name, x.parent.name))
    assert list(deps_list) == [
        Link(ta, tb, relation=DependSuccess),
        Link(ta, tc, relation=DependSuccess, type=All),
        Link(tb, tc, relation=DependFailure, type=All),
        Link(ta, td, relation=DependSuccess, type=Any),
        Link(tb, td, relation=DependSuccess, type=Any),
    ]
    assert str(deps)
    assert repr(deps)