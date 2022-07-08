
#from redengine.core.time.base import CLS
from ._time import parse_time_string

from .utils import ParserPicker

def _parse_time_string(s:str, **kwargs):
    time = parse_time_string(s, **kwargs)
    time._str = s
    return time

parse_time = ParserPicker(
    {
        str: _parse_time_string,
    }
) 