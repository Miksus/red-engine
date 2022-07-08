

class CondParser:
    "Utility class for parsing a condition item"
    cache = {}
    def __init__(self, func, session, cached=False):
        self.func = func
        self.session = session
        self.cached = cached
    
    def __call__(self, s:str, *args, **kwargs):
        session = self.session
        if self.cached and s in session._cond_cache:
            return session._cond_cache[s]

        cond = self.func(*args, **kwargs)
        if self.cached:
            session._cond_cache[s] = cond
        return cond