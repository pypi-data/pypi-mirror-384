import shlex
from typing import Union
import parsegument
from parsegument import Argument

for i in shlex.split("test \"['idk', 3]\" 4"):
    print(i)