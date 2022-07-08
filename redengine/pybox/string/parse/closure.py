
import re

class ClosureParser:
    """

    Manipulate closures, ie. bracets/parentheses/etc.

    Examples:
    ---------
        parser = ClosureParser("(", ")")
        parser.reduce("x + ( 5 * (x / y) + 5)", lambda c: c[1:-2])
        >>> "x +  5 * x / y + 5"

    """
    # TODO: Test

    # TODO: get offsets (closure len) using match for better regex support
    # TODO: check if next_closure is opening/closing using regex
    # TODO: .apply(string, func) : Visit all closures and apply the function
    
    def __init__(self, opening="(", closing=")", regex=False):
        self.opening = opening
        self.closing = closing
        self.regex = regex
        if regex:
            self._regex_opening = re.compile(opening)
            self._regex_closing = re.compile(closing)
        
    def to_list(self, string):
        "Turn the string to (nested) list of strings of closures"
        # "1 * (21 + (211 - 212) / 22) ^ 3 * (21 + (211 - 212) / 22)"
        # --> ("1 * ", ("21 + ", ("211 - 212",), " / 22"), " ^ 3")
        res = []

        len_open = len(self.opening)
        len_close = len(self.closing)
        while self.count(string):

            start, end = self.find_outer_indices(string)

            # Add left residual
            if string[:start]:
                res.append(string[:start])

            substr = string[slice(start + len_open, end)]
            subres = self.to_list(substr)
            res.append(subres)
            string = string[end+len_close:]

        # Add residual
        if string:
            res.append(string)
        return res

    def find_outer_indices(self, string, start=None):
        "Find indices of next outer closure (ie. '(... (...) ...)')"
        # Start of the fetch (searches from left to right)
        offset = len(self.opening)
        start = 0 if start is None else start
        start -= offset
        
        openings = 0
        closings = 0
        while openings != closings or openings == 0:
            
            index, next_closure = self._get_next_element(string, start + offset)

            if next_closure == self.opening:
                openings += 1
                if openings == 1:
                    opening = index
                offset = len(self.opening)
            elif next_closure == self.closing:
                closings += 1
                closing = index
                offset = len(self.closing)

            start = index
        
        return (opening, closing)
    
    def find(self, string, start=None):
        s, e = self.find_outer_indices(string, start)
        return string[s:e+len(self.closing)]
    
    def count(self, string):
        "Count number of closures in the string"
        return string.count(self.opening)
        
    def _get_next_element(self, string, start=None, end=None):
        closures = (self.opening, self.closing)
        indexes = {
            string.index(substr, start, end): substr
            for substr in closures
            if substr in string[start:end]
        }
        minimum = min(indexes)
        return minimum, indexes[minimum]
    
        