
from typing import Callable, Dict, Type, Union
import inspect

class ParserPicker:
    "Chooses parser depending of conf type"
    def __init__(self, type_parsers, subparsers=None, key_as=None):
        self.type_parsers = type_parsers
        self.subparsers = subparsers
        self.key_as = key_as

    def __call__(self, conf, **kwargs):
        "Parse item"
        parser = self.type_parsers[type(conf)]
        return parser(conf, **kwargs)
