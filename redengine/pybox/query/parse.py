
from typing import List
from collections import Counter

from .base import (
    Expression,
    QueryBase,
    Key,
    All, Any, Not,
    Equal, NotEqual, Greater, GreaterEqual, Less, LessEqual,
    true, false, Boolean
)
from .string import Regex

class Parser:
    """Parse various formats to a generic query language
    
    The query language is used to translate filtering
    from conditions to loggers and APIs to the session
    in a uniform way.
    """
    
    operators = {
        'min': GreaterEqual,
        'max': LessEqual,
        'not': NotEqual,
        'regex': Regex,
    }
    def _get_operation(self, key, val):
        if '$' in key:
            key, oper = key.split('$')
            cls_oper = self.operators[oper]
            return cls_oper(Key(key), val)
        else:
            return Equal(Key(key), val)

    def from_dict(self, d:dict):
        """Parse query from dict
        
        Examples
        --------
        >>> from redengine.pybox.query import parser
        >>> qry = parser.from_dict({
        ...     'mydate$min': '2021-07-01',
        ...     'mydate$max': '2021-07-15',
        ...     'mykey1': 10,
        ...     'mystring$regex': r'all of .+',
        ...     'mykey2$not': 'not this',
        ... })
        >>> str(qry)
        "((<mydate> >= '2021-07-01') & (<mydate> <= '2021-07-15') & (<mykey1> == 10) & re.match('all of .+', <mystring>) & (<mykey2> != 'not this'))"
        """
        statement = None

        for key, val in d.items():
            substatement = self._get_operation(key, val)
                
            if statement is None:
                statement = substatement
            else:
                statement &= substatement

        if statement is None:
            return true
        return statement

    def from_tuples(self, l:List[tuple]):
        """Parse query from list of tuples
        
        Examples
        --------
        >>> from redengine.pybox.query import parser
        >>> qry = parser.from_tuples([
        ...     ('mydate$min', '2021-07-01'),
        ...     ('mydate$max', '2021-07-15'),
        ...     ('mykey3', 'this'),
        ...     ('mykey3', 'that')
        ... ])
        >>> str(qry)
        "((<mydate> >= '2021-07-01') & (<mydate> <= '2021-07-15') & ((<mykey3> == 'this') | (<mykey3> == 'that')))"
        """
        key_count = Counter(item[0] for item in l)
        multi = []
        statement = None
        for key, val in l:
            substatement = self._get_operation(key, val)
            if key_count[key] > 1:
                multi.append(substatement)
                continue

            if statement is None:
                statement = substatement
            else:
                statement &= substatement

        if multi:
            substatement = Any(*multi)
            if statement is None:
                statement = substatement
            else:
                statement &= Any(*multi)

        if statement is None:
            return true
        return statement

    def from_kwargs(self, **kwargs):
        """Parse query from Pythonic keyword arguments

        Examples
        --------
        >>> from redengine.pybox.query import parser
        >>> qry = parser.from_kwargs(
        ...     mydate=('2021-07-01', '2021-07-15'),
        ...     mykey='this'
        ... )
        >>> str(qry)
        "((<mydate> >= '2021-07-01') & (<mydate> <= '2021-07-15') & (<mykey> == 'this'))"
        """
        statement = None

        for key, val in kwargs.items():
            if isinstance(val, tuple):
                # A range
                min_, max_ = val
                if min_ is not None and max_ is not None:
                    substatement = GreaterEqual(Key(key), min_) & LessEqual(Key(key), max_)
                elif min_ is not None:
                    substatement = GreaterEqual(Key(key), min_)
                elif max_ is not None:
                    substatement = LessEqual(Key(key), max_)
                else:
                    continue
            elif isinstance(val, list):
                substatement = Any(*(Key(key) == subval for subval in val))
            else:
                substatement = Equal(Key(key), val)
                
            if statement is None:
                statement = substatement
            else:
                statement &= substatement

        if statement is None:
            return true
        return statement
