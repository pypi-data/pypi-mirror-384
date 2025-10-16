import sys, os
from os import walk

current_dir = os.path.dirname(__file__)
# Automatically add all py files as modules
__all__ = []
for f in os.listdir(current_dir):
    if f.endswith(".py"):
        filename = os.path.basename(f)
        if filename != "__init__.py" and (not filename.startswith("main_")):
            __all__.append(filename[0:-3])
