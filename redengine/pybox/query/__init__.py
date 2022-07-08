from .base import (
    #Query,
    Key,
    All, Any, Not,
    Equal, NotEqual, Greater, GreaterEqual, Less, LessEqual
)
from .parse import Parser
from .string import Regex
parser = Parser()
from_dict_string = parser.from_dict