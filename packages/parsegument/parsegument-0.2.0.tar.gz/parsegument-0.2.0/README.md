# Parsegument
An easy to use Argument Parsing and Command Routing library

Read The Docs: https://ryanstudio.dev/docs/parsegument

## Installation
```commandline
pip install parsegument
```

## Quick Start
```python
import parsegument as pg
parser = pg.Parsegumenter() # Create Parsegumenter

group1 = pg.CommandGroup("group1") # Define a Group
parser.add_child(group1) # Add the Group to the main Parsegumenter

@group1.command # Add decorator to create command
def foo(bar:str):
    print(bar)

parser.execute("group1 foo bar_string") # Execute string
```

