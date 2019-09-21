from collections import defaultdict, OrderedDict
import pkgutil
import inspect
import json
import logging
log = logging.getLogger("brick")


def getBlueprintDir():
    return "E:/git/brick/brick/test/templates"

def getBuildDir():
    """
    get build directory path in sandbox.
    """
    import tempfile
    return tempfile.gettempdir()

def loadData(blueprintPath):
    """
    return loaded content of file.
    """
    with open(blueprintPath, 'r') as fd:
        return json.load(fd, object_pairs_hook=OrderedDict)

def getClasses(baseClass):
    classList = []
    from brick import base

    for name, obj in inspect.getmembers(base, inspect.isclass):
        if issubclass(obj, baseClass):
            classList.append(obj)

    return classList


def getBlockClassByName(className):
    for block in getBlockClasses():
        if block.__name__ == className:
            return block


def getBuilderClassesByName(className):
    for builder in getBuilderClasses():
        if builder.__name__ == className:
            return builder


def getBlockClasses():
    from brick.base import Block
    from brick import blocks

    classes = []
    for importer, modname, ispkg in pkgutil.iter_modules(blocks.__path__):
        module = importer.find_module(modname).load_module(modname)
        for name, member in inspect.getmembers(module, inspect.isclass):
            if issubclass(member, Block) and member.isValidClass():
                classes.append(member)

    return classes


def getBuilderClasses():
    from brick.base import Builder
    return getClasses(Builder)


def collectBlocksByCategory():
    blockClasses = getBlockClasses()

    clsmap = defaultdict(list)

    for opcls in blockClasses:
        if not opcls.isValidClass():
            continue

        clsmap[opcls.category].append(opcls)

    return clsmap
