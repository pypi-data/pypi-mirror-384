from __future__ import annotations
from typing import Union, Any
from .BaseGroup import BaseGroup
from .error import NodeDoesNotExist, ArgumentGroupNotFound, MultipleChildrenFound
import shlex


class Parsegumenter(BaseGroup):
    """
    Child class of BaseGroup
    Essentially acts as an extension of CommandGroup
    """
    def __init__(self, name:str="", prefix:str="") -> None:
        super().__init__(name)
        self.children = {}
        self.prefix = prefix

    def _check_valid(self, command: list[str]) -> bool:
        """Checks if the first term of a command is valid based on the name and prefix"""
        first = command[0]
        if self.prefix and not first.startswith(self.prefix): return False
        else: first = first[len(self.prefix):]
        if self.name and first != self.name: return False
        else: return True

    def execute(self, command:Union[str, list[str]]) -> Union[Any, None]:
        """Checks if a child with the name of the first list item exists, then executes the child
        It will also automatically check if it is valid with the prefix and name"""
        parsed = shlex.split(command) if isinstance(command, str) else command
        if not self._check_valid(parsed): return None
        if self.name: parsed.pop(0)
        child_name = parsed[0]
        arguments = parsed[1:]
        child_command = self.children.get(child_name)
        if not child_command:
            return None
        return child_command.execute(arguments)


