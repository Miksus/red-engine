

from datetime import datetime
from typing import Union
from abc import abstractmethod

import pandas as pd

from .utils import to_nanoseconds, timedelta_to_str, to_dict
from .base import TimeInterval


class AnchoredInterval(TimeInterval):
    """Base class for interval for those that have 
    fixed time unit (that can be converted to nanoseconds).

    Converts start and end to nanoseconds where
    0 represents the beginning of the interval
    (ie. for a week: monday 00:00 AM) and max
    is number of nanoseconds from start to the
    end of the interval.
    
    Examples for start=0 nanoseconds
        - for a week: Monday
        - for a day: 00:00
        - for a month: 1st day
    

    Methods:
    --------
        anchor_dict --> int : Calculate corresponding nanoseconds from dict
        anchor_str --> int : Calculate corresponding nanoseconds from string
        anchor_int --> int : Calculate corresponding nanoseconds from integer

    Properties:
        start --> int : Nanoseconds on the interval till the start
        end   --> int : Nanoseconds on the interval till the end 

    Class attributes:
    -----------------
        _scope [str] : 
    """
    components = ("year", "month", "week", "day", "hour", "minute", "second", "microsecond", "nanosecond")

    _fixed_components = ("week", "day", "hour", "minute", "second", "microsecond", "nanosecond")

    _scope = None # ie. day, hour, second, microsecond
    _scope_max = None

    def __init__(self, start=None, end=None, time_point=None):
        #self.start = start
        #self.end = end
        # time_point = True if start is None and end is None else time_point
        self.set_start(start)
        self.set_end(end, time_point=time_point)

    def anchor(self, value, **kwargs):
        "Turn value to nanoseconds relative to scope of the class"
        if isinstance(value, dict):
            # {"hour": 10, "minute": 20}
            return self.anchor_dict(value, **kwargs)

        elif isinstance(value, int):
            # start is considered as unit of the second behind scope
            return self.anchor_int(value, **kwargs)

        elif isinstance(value, str):
            return self.anchor_str(value, **kwargs)
        raise TypeError(value)

    def anchor_int(self, i, **kwargs):
        return to_nanoseconds(**{self._scope: i})

    def anchor_dict(self, d, **kwargs):
        comps = self._fixed_components[(self._fixed_components.index(self._scope) + 1):]
        kwargs = {key: val for key, val in d.items() if key in comps}
        return to_nanoseconds(**kwargs)

    def anchor_dt(self, dt: Union[datetime, pd.Timestamp], **kwargs) -> int:
        "Turn datetime to nanoseconds according to the scope (by removing higher time elements)"
        components = self.components
        components = components[components.index(self._scope) + 1:]
        d = to_dict(dt)
        d = {
            key: val
            for key, val in d.items()
            if key in components
        }

        return to_nanoseconds(**d)

    def set_start(self, val):
        if val is None:
            ns = 0
        else:
            ns = self.anchor(val, side="start")
        self._start = ns
        self._start_orig = val

    def set_end(self, val, time_point=False):
        if time_point and val is None:
            # Interval is "at" type, ie. on monday, at 10:00 (10:00 - 10:59:59)
            ns = self._start + self._unit_resolution - 1
        elif val is None:
            ns = self._scope_max            
        else:
            ns = self.anchor(val, side="end")

        has_time = (ns % to_nanoseconds(day=1)) != 0

        self._end = ns
        self._end_orig = val

    @property
    def start(self):
        delta = pd.Timedelta(self._start, unit="ns")
        repr_scope = self.components[self.components.index(self._scope) + 1]
        return timedelta_to_str(delta, default_scope=repr_scope)

    @start.setter
    def start(self, val):
        self.set_start(val)

    @property
    def end(self):
        delta = pd.Timedelta(self._end, unit="ns")
        repr_scope = self.components[self.components.index(self._scope) + 1]
        return timedelta_to_str(delta, default_scope=repr_scope)

    @end.setter
    def end(self, val):
        self.set_end(val)

    @abstractmethod
    def anchor_str(self, s, **kwargs) -> int:
        raise NotImplementedError

    def __contains__(self, dt) -> bool:
        "Whether dt is in the interval"

        ns_start = self._start
        ns_end = self._end

        if ns_start == ns_end:
            # As there is no time in between, 
            # the interval is considered full
            # cycle (ie. from 10:00 to 10:00)
            return True

        ns = self.anchor_dt(dt) # In relative nanoseconds (removed more accurate than scope)

        is_over_period = ns_start > ns_end # period is overnight, over weekend etc.
        if not is_over_period:
            return ns_start <= ns <= ns_end
        else:
            return ns >= ns_start or ns <= ns_end

    def get_scope_back(self, dt):
        "Override if offsetting back is different than forward"
        return self._scope_max + 1

    def get_scope_forward(self, dt):
        "Override if offsetting back is different than forward"
        return self._scope_max + 1

    def rollstart(self, dt):
        "Roll forward to next point in time that on the period"
        if dt in self:
            return dt
        else:
            return self.next_start(dt)

    def rollend(self, dt):
        "Roll back to previous point in time that is on the period"
        if dt in self:
            return dt
        else:
            return self.prev_end(dt)

    def next_start(self, dt):
        "Get next start point of the period"
        ns = self.anchor_dt(dt) # In relative nanoseconds (removed more accurate than scope)
        ns_start = self._start
        ns_end = self._end

        if ns < ns_start:
            # not in period, over night
            #                     dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, earlier than start
            #          dt                              
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            
            # in period, over night, earlier than start
            #            dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end
            offset = pd.Timedelta(int(ns_start) - int(ns), unit="ns")
        else:
            # not in period, later than start
            #      dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start

            # in period, over night, later than start
            #       dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # in period
            #                    dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            ns_scope = self.get_scope_forward(dt)
            offset = pd.Timedelta(int(ns_start) - int(ns) + ns_scope, unit="ns")
        return dt + offset

    def next_end(self, dt):
        "Get next end point of the period"
        ns = self.anchor_dt(dt) # In relative nanoseconds (removed more accurate than scope)
        ns_start = self._start
        ns_end = self._end

        if ns <= ns_end:
            # in period
            #                    dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            
            # in period, over night, earlier than end
            #            dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, earlier than end
            #          dt                              
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            offset = pd.Timedelta(int(ns_end) - int(ns), unit="ns")
        else:
            # not in period, over night
            #                     dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, later than end
            #      dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start

            # in period, over night, later than end
            #       dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end
            ns_scope = self.get_scope_forward(dt)
            offset = pd.Timedelta(int(ns_end) - int(ns) + ns_scope, unit="ns")
        return dt + offset

    def prev_start(self, dt):
        "Get previous start point of the period"
        ns = self.anchor_dt(dt) # In relative nanoseconds (removed more accurate than scope)
        ns_start = self._start
        ns_end = self._end

        if ns < ns_start:
            # not in period, over night
            #                     dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, earlier than start
            #          dt                              
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            
            # in period, over night, earlier than start
            #            dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end
            ns_scope = self.get_scope_back(dt)
            offset = pd.Timedelta(int(ns_start) - int(ns) - ns_scope, unit="ns")
        else:
            # not in period, later than start
            #      dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start

            # in period, over night, later than start
            #       dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # in period
            #                    dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            offset = pd.Timedelta(int(ns_start) - int(ns), unit="ns")
        return dt + offset

    def prev_end(self, dt):
        "Get pervious end point of the period"
        ns = self.anchor_dt(dt) # In relative nanoseconds (removed more accurate than scope)
        ns_start = self._start
        ns_end = self._end

        if ns < ns_end:
            # in period
            #                    dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            
            # in period, over night, earlier than end
            #            dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, earlier than end
            #          dt                              
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start
            ns_scope = self.get_scope_back(dt)
            offset = pd.Timedelta(int(ns_end) - int(ns) - ns_scope, unit="ns")
        else:
            # not in period, over night
            #                     dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end

            # not in period, later than end
            #      dt             
            # --<---------->-----------<-------------->--
            #  end   |   start        end    |      start

            # in period, over night, later than end
            #       dt
            #  -->----------<----------->--------------<-
            #  start   |   end        start     |     end
            offset = pd.Timedelta(int(ns_end) - int(ns), unit="ns")

        return dt + offset

    def __repr__(self):
        cls_name = type(self).__name__
        return f'{cls_name}({repr(self._start_orig)}, {repr(self._end_orig)})'

    def __str__(self):
        # Hour: '15:'
        start_ns = self._start
        end_ns = self._end

        scope = self._scope
        repr_scope = self.components[self.components.index(self._scope) + 1]

        to_start = pd.Timedelta(start_ns, unit="ns")
        to_end = pd.Timedelta(end_ns, unit="ns")

        start_str = timedelta_to_str(to_start, default_scope=repr_scope)
        end_str = timedelta_to_str(to_end, default_scope=repr_scope)

        start_str = f"0 {repr_scope}s" if not start_str else start_str
        return f"{start_str} - {end_str}"
