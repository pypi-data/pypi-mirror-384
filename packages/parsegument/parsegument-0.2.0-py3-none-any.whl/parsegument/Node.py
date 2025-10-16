class Node:
    """Base Node class"""
    def __init__(self, name:str) -> None:
        self.name = name

    def execute(self, arguments: list):
        raise NotImplementedError