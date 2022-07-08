
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redengine import Session

class RedBase:
    """Baseclass for all Red Engine classes"""
    session: 'Session' = None