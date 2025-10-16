from __future__ import annotations
from typing import Union, Callable, TYPE_CHECKING
from inspect import signature
from .utils.convert_params import convert_param
from .Node import Node
from .Command import Command

if TYPE_CHECKING:
    from .CommandGroup import CommandGroup


class BaseGroup:
    def __init__(self, name:str):
        self.name = name
        self.children = {}

    @classmethod
    def _get_methods(cls):
        return set([i for i in dir(cls) if i[0] != "_"])

    def add_child(self, child: Union[Command, CommandGroup]):
        """Add a Command or CommandGroup as a child"""
        if child.name in [i.name for i in self.children]:
            return False
        self.children[child.name] = child
        return True

    def command(self, func: Callable):
        """A Decorator that automatically creates a command, and adds it as a child"""
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        params = signature(func).parameters
        func_name = func.__name__
        command_object = Command(name=func_name, executable=func)
        for key, param in params.items():
            converted = convert_param(param)
            command_object.add_node(converted)
        self.add_child(command_object)
        return wrapper

    def execute(self, nodes: Union[str, list[str]]):
        raise NotImplementedError

