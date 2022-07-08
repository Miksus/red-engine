
from typing import Tuple, Dict
import inspect

# Copied from redengine.pybox\meta\func\func.py

def filter_keyword_args(_func, _params:dict=None, **kwargs):
    """Filter only keyword arguments that the 
    function requires."""
    if _params:
        kwargs.update(_params)
    sig = inspect.signature(_func)

    kw_args = [
        val.name
        for name, val in sig.parameters.items()
        if val.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD, # Normal argument
            inspect.Parameter.KEYWORD_ONLY # Keyword argument
        )
    ]
    return {
        key: val for key, val in kwargs.items()
        if key in kw_args
    }
