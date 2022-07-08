
import re
from typing import Pattern
from .base import Expression, Key

class Regex(Expression):
    """Regex expression

    Parameters
    ----------
    regex : Pattern
        Regex pattern
    key : Key
        Value of the key to match

    Examples
    --------

    .. code-block:: python

        Regex(Key('mycol'), regex=r'this .+ thing')
    """
    def __init__(self, key:Key, regex:Pattern):
        self.key = key
        self.regex = regex

    def match(self, item:dict):
        return bool(re.match(self.regex, self.key.get_value(item)))

    def __str__(self):
        return f're.match({repr(self.regex)}, {str(self.key)})'