
from redengine.core.parameters import BaseArgument

class Private(BaseArgument):
    """Private argument not meant to be shown outside.
    
    The value of the argument is hidden from else except
    tasks.
    """

    string_hidden = "*****"

    def __init__(self, value):
        self.__value = value

    def get_value(self, task=None):
        if task is None:
            return self.string_hidden
        else:
            # Called for task --> must pass the actual value
            return self.__value

    def __eq__(self, other):
        if isinstance(other, Private):
            return self.__value == other._Private__value
        else:
            return self.__value == other

    def __repr__(self):
        cls_name = type(self).__name__
        return f'{cls_name}({self.string_hidden})'

    def __str__(self):
        return self.string_hidden