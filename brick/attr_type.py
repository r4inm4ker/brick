"""custom classes for attribute type recognition when saving and reloading attribute from blueprint
"""
import sys
from collections import OrderedDict
import inspect

if sys.version_info[0] > 2:
    unicode = str
else:
    unicode = unicode

class BrickAttr(object):
    @classmethod
    def evaluate(cls, name, value, parent_locals=None):
        return value

class String(BrickAttr, unicode):
    pass

class Int(BrickAttr, int):
    pass

class Float(BrickAttr, float):
    pass

class Bool(BrickAttr, float):
    pass

class List(BrickAttr, list):
    pass

class Dict(BrickAttr, OrderedDict):
    pass

class Input(BrickAttr, tuple):
    pass

class Script(BrickAttr, unicode):
    pass

class Path(BrickAttr, unicode):
    pass

class Chooser(BrickAttr, unicode):
    pass

class TypeChosser(Chooser):
    pass


class NamedObject(BrickAttr, object):
    @classmethod
    def evaluate(cls, name, value, parent_locals=None):
        copyLocals = OrderedDict()

        for key,val in parent_locals.items():
            copyLocals[key] = val

        for key,val in locals().items():
            copyLocals[key] = val

        exec (value, None, copyLocals)
        for key, val in copyLocals.items():
            # right now, support the assignment name to be either the variable name itself, or "self"
            if key == name or key == "self":
                return val


def getTypeFromName(typeName):
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(obj,BrickAttr):
            if name == typeName:
                return obj


def guessNameFromValue(value):
    if isinstance(value,(str,unicode)):
        return String.__name__
    elif isinstance(value,int):
        return Int.__name__
    elif isinstance(value,float):
        return Float.__name__
    elif isinstance(value,bool):
        return Bool.__name__
    elif isinstance(value,list):
        return List.__name__
    elif isinstance(value,(dict,OrderedDict)):
        return Dict.__name__
    else:
        raise ValueError("cannot guess value type {} ({})".format(value,type(value)))