import parsegument as pg
from parsegument import CommandGroup

class ChildGroup(CommandGroup):
    def __init__(self):
        super().__init__("ChildGroup")

    @staticmethod
    def method_thing(test:str):
        return test + ", This is a method thing"

    def initialise(self):
        method_thing = pg.Command("method_thing", self.method_thing)
        method_thing.add_node(pg.Argument("test", str))
        self.add_child(method_thing)

parser = pg.Parsegumenter()
group = ChildGroup()
group.initialise()
parser.add_child(group)
print(parser.execute("ChildGroup method_thing testfrfr"))