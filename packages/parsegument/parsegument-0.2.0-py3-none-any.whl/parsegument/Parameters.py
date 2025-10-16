from .Node import Node

class Parameter(Node):
    """Base Parameter class"""
    def __init__(self, name: str, arg_type:type) -> None:
        super().__init__(name)
        self.arg_type = arg_type


class Argument(Parameter):
    """A Compulsory Argument"""
    def __init__(self, name: str, arg_type:type=str) -> None:
        super().__init__(name, arg_type)
        self.arg_type = arg_type

class Flag(Parameter):
    """An optional boolean kwarg"""
    def __init__(self, name:str) -> None:
        super().__init__(name, bool)

class Operand(Parameter):
    """Any keyword Argument"""
    def __init__(self, name: str, arg_type:type=str) -> None:
        super().__init__(name, arg_type)

