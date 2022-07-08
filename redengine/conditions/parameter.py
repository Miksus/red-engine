
import re
from typing import Union

from redengine.core.condition import BaseCondition


class IsEnv(BaseCondition):
    """Condition checks whether session parameter `env`
    has the given value. 

    Parameters
    ----------
    env : str
        The environment to be set in order to the condition
        to be ``True``.

    Examples
    --------
    >>> from redengine.conditions import IsEnv
    >>> is_prod = IsEnv("prod")

    >>> # Correct environment
    >>> from redengine import session
    >>> session.env = 'prod'
    >>> bool(is_prod)
    True

    >>> # Incorrect environment
    >>> session.env = 'dev'
    >>> bool(is_prod)
    False
    """
    __parsers__ = {re.compile(r"env '(?P<env>.+)'"): "__init__"}

    def __init__(self, env):
        self.env = env
    
    def __bool__(self):
        return self.session.parameters.get("env", None) == self.env

class ParamExists(BaseCondition):
    """Condition to check whether parameter(s) (and their values)
    exists from ``session.parameters``.

    Parameters
    ----------
    *args : iterable of strings
        Names of the parameters expected to be 
        found from the session (in order the 
        condition to be True)
    **kwargs : dict
        Names of the parameters and their values 
        expected from the session (in order the 
        condition to be True)

    Examples
    --------
    >>> from redengine.conditions import ParamExists
    >>> condition = ParamExists("z", x=1, y=2)
    
    >>> # Parameters found
    >>> from redengine import session
    >>> session.parameters = {"x": 1, "y": 2, "z": 3, "k": 4}
    >>> bool(condition)
    True

    >>> # Missing parameter(s)
    >>> session.parameters = {"x": 1}
    >>> bool(condition)
    False
    """
    __parsers__ = {
        re.compile(r"param '(?P<l>.+)' exists"): "_from_list",
        re.compile(r"param '(?P<key>.+)' is '(?P<value>.+)'"): "_from_key_value",
    }

    param_keys:dict
    param_vals:tuple

    def __init__(self, *args, **kwargs):
        self.param_keys = args
        self.param_values = kwargs
    
    def __bool__(self):
        params = self.session.parameters
        for key in self.param_keys:
            if key not in params:
                return False
        for key, val in self.param_values.items():
            if key not in params:
                return False
            elif params[key] != val:
                return False
        # Passed all test
        return True

    @classmethod
    def _from_list(cls, l:Union[tuple, list]):
        return cls(*l)
    
    @classmethod
    def _from_key_value(cls, key:str, value):
        return cls(**{key: value})