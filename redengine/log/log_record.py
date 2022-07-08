import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class MinimalRecord(BaseModel):
    """A log record with minimal number of fields for Red Engine to work"""
    task_name: str
    action: str = Field(description="Scheduler action: 'run', 'success', 'fail'")
    created: float

class LogRecord(MinimalRecord):
    """A logging record

    See attributes: https://docs.python.org/3/library/logging.html#logrecord-attributes
    """
    name: str
    msg: str
    levelname: str
    levelno: int
    pathname: str
    filename: str
    module: str
    exc_text: Optional[str] = Field(description="Exception text")
    lineno: int
    funcName: str
    created: float
    msecs: float
    relativeCreated: float
    thread: int
    threadName: str
    processName: str
    process: int
    message: str

    formatted_message: str = Field(description="Formatted message. This field is created by RepoHandler.")

class TaskLogRecord(MinimalRecord):

    start: Optional[datetime.datetime]
    end: Optional[datetime.datetime]
    runtime: Optional[datetime.timedelta]

    message: str
    exc_text: Optional[str]