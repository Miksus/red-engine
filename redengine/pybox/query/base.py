from typing import Iterable, Iterator
import datetime
import pandas as pd

class QueryBase:
    
    def _get_value(self, item:dict, oper):
        return item[oper.name] if isinstance(oper, Key) else oper
    
    def filter(self, data:Iterable[dict]) -> Iterator[dict]:
        "Filter iterable of dicts"
        for dict in data:
            if self.match(dict):
                yield dict
    
    def to_pykwargs(self):
        """Put the query to simple Python keyword representation"""

        def _get_key_value(left, right):
            is_left_key = isinstance(left, Key)
            is_right_key = isinstance(right, Key)
            if is_left_key and is_right_key:
                raise ValueError("Both cannot be keys")
            elif is_left_key:
                return left.name, right
            elif is_right_key:
                return right.name, left
            else:
                raise ValueError("Neither are keys")
        py_query = {}
        qry = self
        if self == true:
            return {}
        if not isinstance(self, All):
            qry = (self,)
        for sub_qry in qry:
            if isinstance(sub_qry, Equal):
                key, value = _get_key_value(sub_qry.left, sub_qry.right)
                py_query[key] = value
            elif isinstance(sub_qry, (GreaterEqual, LessEqual)):
                key, value = _get_key_value(sub_qry.left, sub_qry.right)
                past_min_val = py_query.get(key, (None, None))[0]
                past_max_val = py_query.get(key, (None, None))[1]
                if isinstance(sub_qry, LessEqual):
                    min_val = past_min_val
                    max_val = value
                elif isinstance(sub_qry, GreaterEqual):
                    min_val = value
                    max_val = past_max_val
                py_query[key] = (min_val, max_val)
            else:
                raise TypeError(f"No conversion for type: {type(sub_qry)}")
        return py_query


class Key(QueryBase):
    """Key of a data dictionary"""
    def __init__(self, name):
        self.name = name
        
    def __eq__(self, other):
        return Equal(self, other)
    
    def __ne__(self, other):
        return NotEqual(self, other)
    
    def __gt__(self, other):
        return Greater(self, other)
    
    def __lt__(self, other):
        return Less(self, other)
    
    def __ge__(self, other):
        return GreaterEqual(self, other)
    
    def __le__(self, other):
        return LessEqual(self, other)

    def __repr__(self):
        return f'Key({repr(self.name)})'
    
    def __str__(self):
        return f'<{self.name}>'
    
    def get_value(self, d:dict):
        return d[self.name]

class Expression(QueryBase):
    """Base class for query expressions"""
    def __and__(self, other):
        if not isinstance(self, All):
            self = (self,)
        if not isinstance(other, All):
            other = (other,)
        return All(*self, *other)
    
    def __or__(self, other):
        if not isinstance(self, Any):
            self = (self,)
        if not isinstance(other, Any):
            other = (other,)
        return Any(*self, *other)
    
    def __invert__(self):
        return Not(self)

    def _to_comparable(self, left, right):
        dt_cls = (datetime.datetime, pd.Timestamp) # Note we test pd.Timestamp due to test mocking
        is_datetime = isinstance(left, dt_cls) or isinstance(right, dt_cls)
        if is_datetime:
            return pd.Timestamp(left), pd.Timestamp(right)
        else:
            return left, right
    
class All(Expression):
    
    def __init__(self, *args):
        self.args = args
        
    def match(self, item:dict):
        return all(arg.match(item) for arg in self.args)

    def __iter__(self):
        return iter(self.args)
    
    def __repr__(self):
        str_args = ', '.join(repr(arg) for arg in self.args)
        return f'{type(self).__name__}({str_args})'
    
    def __str__(self):
        return '(' + ' & '.join(str(arg) for arg in self.args) + ')'
    
class Any(Expression):
    
    def __init__(self, *args):
        self.args = args
        
    def match(self, item:dict):
        return any(arg.match(item) for arg in self.args)
    
    def __iter__(self):
        return iter(self.args)
    
    def __str__(self):
        return '(' + ' | '.join(str(arg) for arg in self.args) + ')'
    
class Not(Expression):
    
    def __init__(self, right):
        self.right = right
        
    def match(self, item:dict):
        return not self.right.match(item)
    
    def __str__(self):
        return f'~{self.right}'
    

class Equal(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value == right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} == {str(right)}" + ')'

class NotEqual(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value != right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} != {str(right)}" + ')'

class Greater(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value > right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} > {str(right)}" + ')'

class GreaterEqual(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value >= right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} >= {str(right)}" + ')'

class Less(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value < right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} < {str(right)}" + ')'

class LessEqual(Expression):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def match(self, item:dict):
        left_value = self._get_value(item, oper=self.left)
        right_value = self._get_value(item, oper=self.right)
        left_value, right_value = self._to_comparable(left_value, right_value)
        return left_value <= right_value
    
    def __str__(self):
        left, right = self.left, self.right
        left = repr(left) if isinstance(left, str) else str(left)
        right = repr(right) if isinstance(right, str) else str(right)
        return '(' + f"{str(left)} <= {str(right)}" + ')'


class Boolean(Expression):

    def __init__(self, value):
        self.value = value

    def match(self, item:dict):
        return bool(self.value)

true = Boolean(True)
false = Boolean(False)

