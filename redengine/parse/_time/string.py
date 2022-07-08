
from ..utils.string_parser import InstructionParser
from redengine.core.time import Any, All
from .time_item import parse_time_item

def _flatten(*args, types, with_attr):
    comps = []
    for arg in args:
        if isinstance(arg, types):
            comps += getattr(arg, with_attr)
        else:
            comps.append(arg)
    return comps

def _parse_any(*args):
    comps = _flatten(*args, types=Any, with_attr="periods")
    return Any(*comps)

def _parse_all(*args):
    comps = _flatten(*args, types=All, with_attr="periods")
    return All(*comps)

parse_time_string = InstructionParser(
    parse_time_item,
    operators=[
        {
            "symbol": "&",
            "func": _parse_all,
            "side": "both",
        },
        {
            "symbol": "|",
            "func": _parse_any,
            "side": "both",
        },
    ]
)