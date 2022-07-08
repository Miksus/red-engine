
from redengine.core.condition.base import CLS_CONDITIONS, BaseCondition
from redengine.conditions import true, false
from ._condition import parse_condition_string
from .utils import ParserPicker

def _parse_condition_string(s:str, **kwargs) -> BaseCondition:
    cond = parse_condition_string(s, **kwargs)
    cond._str = s
    return cond

def _parse_bool(b:bool) -> BaseCondition:
    return true if b else false

PARSER = ParserPicker(
    {
        str: _parse_condition_string,
        bool: _parse_bool
    }
)

def parse_condition(conf, **kwargs):
    if isinstance(conf, BaseCondition):
        return conf
    else:
        return PARSER(conf, **kwargs)