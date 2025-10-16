
from .BaseGroup import BaseGroup
from .error import NodeDoesNotExist

class CommandGroup(BaseGroup):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.children = {}

    @classmethod
    def _get_commands(cls):
        return cls._get_methods() - CommandGroup._get_methods()

    def initialise(self):
        """
        Only use this if you are making a child class of CommandGroup
        This does the same thing as the @BaseGroup.command decorator, but does it for every custom method in the child class
        """
        child_commands = list(self._get_commands())
        methods = [getattr(self, i) for i in child_commands]
        for method in methods:
            self.command(method)

    def execute(self, nodes:list[str]):
        """
        Checks if a child with the name of the first list item exists, then executes the child
        """
        child = self.children.get(nodes[0])
        if not child:
            return None
        return child.execute(nodes[1:])