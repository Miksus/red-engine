
from redengine.time import (
    TimeOfWeek,
    TimeOfDay,
    TimeOfHour,
    TimeOfMinute,
    TimeDelta,
    TimeOfMonth
)

TIME_CLASSES = {
    "monthly": TimeOfMonth,
    "weekly": TimeOfWeek,
    "daily": TimeOfDay,
    "hourly": TimeOfHour,
    "minutely": TimeOfMinute,

    "month": TimeOfMonth,
    "week": TimeOfWeek,
    "day": TimeOfDay,
    "hour": TimeOfHour,
    "minute": TimeOfMinute,

    "this month": TimeOfMonth,
    "this week": TimeOfWeek,
    "today": TimeOfDay,
    "this hour": TimeOfHour,
    "this minute": TimeOfMinute,
}

# Utility funcs
def get_between(type_, start, end):
    type_ = type_.lower()
    cls = TIME_CLASSES[type_]
    return cls(start, end)

def get_after(type_, start):
    type_ = type_.lower()
    cls = TIME_CLASSES[type_]
    return cls(start, None)

def get_before(type_, end):
    type_ = type_.lower()
    cls = TIME_CLASSES[type_]
    return cls(None, end)

def get_on(type_, start):
    type_ = type_.lower()
    cls = TIME_CLASSES[type_]
    return cls(start, time_point=True)

def get_full_cycle(type_, start=None):
    type_ = type_.lower()
    cls = TIME_CLASSES[type_]
    return cls(start, start)


