import re
from typing import Any
import ast
from ..error import ConversionTypeNotFound


def parse_string(string:str) -> list:
    if not string: return []
    opened_quotation = False
    saved_index = 0
    arguments = []
    for idx, letter in enumerate(string):
        if letter == '"' or letter == "'":
            opened_quotation = not opened_quotation
            if opened_quotation:
                saved_index = idx+1
            else:
                arguments.append(string[saved_index:idx])
                saved_index = idx + 1
            continue
        if letter == ' ' and not opened_quotation:
            arguments.append(string[saved_index:idx])
            saved_index = idx + 1
            continue
    if string[saved_index:]:
        arguments.append(string[saved_index:])
    return arguments

def node_type(node:str):
    if node[0] == "-":
        if node[1] == "-":
            return "Operand"
        return "Flag"
    return "Argument"

def parse_operand(operand:str):
    value = re.search("=.*", operand)
    operand_name = re.search(".*=", operand)
    return operand_name.group()[2:-1], value.group()[1:] if value else None

def convert_string_to_result(string:str, arg_type: type) -> Any:
    if arg_type == str or arg_type == int or arg_type == float or arg_type == bool or arg_type == complex:
        return arg_type(string)
    elif arg_type == list or arg_type == tuple or arg_type == dict or arg_type == set:
        return ast.literal_eval(string)
    else:
        raise ConversionTypeNotFound(arg_type)

