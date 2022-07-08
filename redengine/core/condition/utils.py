
from collections.abc import Iterable

from .statement import Statement

def _has_sub_conditions(obj):
    return isinstance(obj, Iterable)

def _set_statement_default(cond, **kwargs):
    if isinstance(cond, Statement):
        for key, default in kwargs.items():
            default_not_set = key not in cond.kwargs or cond.kwargs[key] is None
            if default_not_set:
                cond.kwargs[key] = default

def _set_default(cond, **kwargs):
    if not _has_sub_conditions(cond):
        _set_statement_default(cond, **kwargs)
        return

    for sub_cond in cond:
        if _has_sub_conditions(sub_cond):
            _set_default(sub_cond, **kwargs)
        else:
            _set_statement_default(sub_cond, **kwargs)
    
def set_statement_defaults(cond, **kwargs):
    _set_default(cond, **kwargs)
