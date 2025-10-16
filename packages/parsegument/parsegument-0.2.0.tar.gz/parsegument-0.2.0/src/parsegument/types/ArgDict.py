from typing import Union, List, Dict, TypedDict

ArgType = Union["Argument", "Operand", "Flag", None]

class ArgDict(TypedDict):
    args: List[ArgType]
    kwargs: Dict[str, ArgType]