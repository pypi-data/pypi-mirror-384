import typing
import inspect
from ..Parameters import Argument, Flag, Operand


def convert_params(params: typing.OrderedDict):
    pass

def convert_param(param:inspect.Parameter):
    name = param.name
    param_type = param.annotation
    default = param.default
    arg_type = identify_type(param_type, default)
    if arg_type != Flag:
        final = arg_type(name=name, arg_type=param_type)
        return final
    else:
        return Flag(name=name)

def identify_type(annotation: type, kwarg: typing.Any=None) -> typing.Union[Argument.__class__, Flag.__class__, Operand.__class__]:
    if kwarg == inspect.Parameter.empty:
        return Argument
    if annotation == bool:
        return Flag
    else:
        return Operand
