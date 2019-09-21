"""custom classes for attribute type recognition when saving and reloading attribute from blueprint
"""
import sys

if sys.version_info[0] > 2:
    unicode = str
else:
    unicode = unicode


class Input(tuple):
    pass


class Script(unicode):
    pass

