from .interval import *
from redengine.core.time import TimeDelta, StaticInterval, All, Any

# Syntax
import pandas as pd
import calendar

from .construct import get_between, get_before, get_after, get_full_cycle, get_on

from redengine.session import Session

Session._time_parsers.update(
    {
        re.compile(r"time of (?P<type_>month|week|day|hour|minute) between (?P<start>.+) and (?P<end>.+)"): get_between,
        re.compile(r"time of (?P<type_>month|week|day|hour|minute) after (?P<start>.+)"): get_after,
        re.compile(r"time of (?P<type_>month|week|day|hour|minute) before (?P<end>.+)"): get_before,
        re.compile(r"time of (?P<type_>month|week) on (?P<start>.+)"): get_on,

        re.compile(r"every (?P<past>.+)"): TimeDelta,
        re.compile(r"past (?P<past>.+)"): TimeDelta,
        "always": StaticInterval(),
        "never": StaticInterval(start=StaticInterval.max - StaticInterval.resolution),
    }
)