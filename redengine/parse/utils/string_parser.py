
from functools import partial
import re

from typing import Callable, Dict, List

from redengine.pybox.string.parse import ClosureParser
from redengine.pybox.container.visitor import Visitor


class InstructionParser:

    def __init__(self, item_parser:Callable, operators:List[Dict[str, Callable]]):
        self.item_parser = item_parser

        self.operators = operators
        self.symbols = set([oper["symbol"] for oper in operators])

    def __call__(self, s:str, **kwargs):
        """Parse a string to condition. Allows logical operators.

        Reserved keywords:
            "&" : and operator
            "|" : or operator
            "~" : not operator
            "(" : opening closure
            ")" : closing closure

        These characters cannot be found in
        individual condition parsing (ie. 
        in the names of tasks).
        """
        p = ClosureParser()
        v = Visitor(visit_types=(list,))

        # 1. Split closures
        l = p.to_list(s)

        # 2. Split operations
        v.assign_elements(l, self._split_operations)
        
        # 2a. Remove extra tuples
        v.apply(l, _flatten_tuples)
        
        v.assign_elements(l, partial(self._parse, **kwargs))
        
        e = v.reduce(l, self._assemble) 
        return e

    def _parse(self, __s:tuple, **kwargs):
        s = __s
        def parse_string(s):
            s = s.strip()
            if s in ("&", "|", "~"):
                return s
            else:
                return self.item_parser(s, **kwargs)

        if isinstance(s, str):
            return parse_string(s)
        else:
            return tuple(parse_string(e) for e in s)

    def _assemble(self, *s:tuple):

        v = Visitor(visit_types=(list, tuple))
        s = v.flatten(s)

        #s = self._assemble_not(s)
        #s = self._assemble_and(s)
        #s = self._assemble_or(s)

        for operator in self.operators:
            oper_str = operator["symbol"]
            oper_func = operator["func"]
            oper_side = operator["side"]
            s = self._assemble_oper(s, oper_str=oper_str, oper_func=oper_func, side=oper_side)
        
        # TODO: Clean this mess (but be careful)

        return s[0] if isinstance(s, tuple) else s

    def _assemble_oper(self, s:list, oper_str:str, oper_func:Callable, side="both"):
        s = list(reversed(s))
        while self._contains_operator(s, oper_str):
            pos = self._index(s, [oper_str])

            # Set the comparison object to "|" in the list
            
            if side == "both":
                obj = oper_func(s[pos+1], s[pos-1])
                s[pos] = obj
                # NOTE: We have reversed the "s" thus we also put the arguments to 

                # Remove lhs and rhs of the comparison as they are embedded in comparison object
                del s[pos-1]
                del s[pos+1-1] # We -1 because we already removed one element thus pos is misaligned
            elif side == "right":
                obj = oper_func(s[pos-1])
                s[pos-1] = obj
                del s[pos]
            elif side == "left":
                obj = oper_func(s[pos+1])
                s[pos+1] = obj
                del s[pos]

        return tuple(reversed(s))

    @staticmethod
    def _contains_operator(s:list, oper_str:str):
        for e in s:
            if isinstance(e, str) and e in (oper_str,):
                return True
        return False

    @staticmethod
    def _index(s:list, items:list):
        "Get "
        for i, e in enumerate(s):
            if isinstance(e, str) and e in items:
                return i
        raise KeyError

    def _split_operations(self, s:str):
        # The following are considered as reserved operators
        #   "&" : and operator
        #   "|" : or operator
        #   "~" : not operator
        symbols = ''.join(self.symbols)
        regex = r'([' + symbols + '])'
        s = s.strip()
        if bool(re.search(regex, s)):
            l = re.split(regex, s)
            l = [elem for elem in l if elem.strip()]
            if len(l) == 1:
                # Has only the 
                return l[0]

            return tuple(l)
        else:
            return s


def _flatten_tuples(cont):

    for i, item in enumerate(cont):
        if isinstance(item, tuple):
            cont.pop(i)
            for j, tpl_item in enumerate(item):
                cont.insert(i+j, tpl_item)
    
    return cont


# Conditions

