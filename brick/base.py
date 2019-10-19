import json
from collections import OrderedDict
from lib.path import Path
from .constants import BuildStatus, BLUEPRINT_EXTENSION
from . import attr_type
from brick import lib
import traceback
import time
import uuid
import sys
import logging


log = logging.getLogger("brick")


class Builder(object):
    def __init__(self):
        self.blocks = []
        self.notes = ""
        self._name = ""
        self.attrs = OrderedDict()
        self.resultAttrs = {}
        # TODO: inspect whether self.resultAttrMap and self.results are required for now.
        self.resultAttrMap = {}
        self.results = {}
        self.nextStep = 0

    @property
    def name(self):
        if not self._name:
            self._name =  '{0}_{1}'.format(self.__class__.__name__, str(uuid.uuid4()))
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def insertBlock(self, block, index=-1):
        if index < 0:
            index = len(self.blocks)
        self.blocks.insert(index, block)
        block.parent = self

    def createBlock(self, blockType):
        blockCls = lib.getBlockClassByName(blockType)
        block = blockCls()
        nextUniqueName = self.getNextUniqueName(blockType=blockType)
        block.name = nextUniqueName
        return block

    def getNextUniqueName(self, blockType=None):
        baseName = blockType or "block"
        blockIndex = 1
        while True:
            uname = "{0}{1}".format(baseName, blockIndex)
            for currentBlock in self.blocks:
                if uname == currentBlock.name:
                    blockIndex += 1
                    break
            else:
                # no repeat with existing name
                return uname


    def saveBlueprint(self, bluePrint, notes=""):

        writeData = OrderedDict()

        writeData['notes'] = notes
        writeData['type'] = self.__class__.__name__

        # serialize attrs
        srAttrs = OrderedDict()
        for attrName, val in self.attrs.items():
            attrType, attrVal = str(val[0].__name__), val[1]
            srAttrs[attrName] = (attrType, attrVal)


        writeData['attrs'] = srAttrs

        blocks = []

        for block in self.blocks:
            blocks.append(block.dump())

        writeData['blocks'] = blocks


        with open(bluePrint, 'w') as fd:
            json.dump(writeData, fd, indent=4)

    @classmethod
    def loadBlueprint(cls, bluePrintName):
        filePath = Path(bluePrintName)

        if not filePath.exists():
            # not exists, try searching for file in blueprint directory
            templateDir = lib.getBlueprintDir()
            autoPath = templateDir / filePath
            if not autoPath.endswith(BLUEPRINT_EXTENSION):
                autoPath = autoPath + BLUEPRINT_EXTENSION
            if not autoPath.exists():
                # still not exist, cancel importing
                raise ValueError('blueprint {0} does not exist'.format(bluePrintName))
            else:
                filePath = autoPath

        with open(filePath, 'r') as fd:
            blueprint = json.load(fd, object_pairs_hook=OrderedDict)

        return cls.load(blueprint)

    def setAttr(self, key, typeVal):
        self.attrs[key] = typeVal

    def connectInputs(self, key, node, attr):
        self.inputAttrs[key] = (node.name, attr)
        self.resultAttrMap[node.name] = key

    @classmethod
    def load(cls, data):
        builderCls = lib.getBuilderClassesByName(data.get('type'))

        builder = builderCls()

        rawAttrs = data.get('attrs')

        convertedAttrs = OrderedDict()

        for attrName, typeVal in rawAttrs.items():
            # for old format compatibility with no attrType stored
            # can be removed in the future when all the blueprints have been updated to have attrType
            if not isinstance(typeVal, (list,tuple)):
                attrType = attr_type.guessNameFromValue(typeVal)
                typeVal = (attrType, typeVal)
            #############################################################################

            attrType = attr_type.getTypeFromName(typeVal[0])

            convertedAttrs[attrName] = (attrType, typeVal[1])

        builder.attrs = convertedAttrs

        for blockData in data.get('blocks'):
            block = Block.load(blockData)
            builder.insertBlock(block)

        return builder

    def reset(self):
        self.nextStep = 0
        for op in self.blocks:
            op.reset()

    def syncOrder(self, order):
        nameMap = {block.name: block for block in self.blocks}
        newList = [nameMap.get(name, None) for name in order if nameMap.get(name, None)]
        self.blocks = newList

    def rewind(self):
        self.nextStep = 0

    def buildNext(self):
        try:
            block = next(self.iterBlocks())

            if block:
                self.doTheRunning(block)

                if block.buildStatus == BuildStatus.fail:
                    self.nextStep -= 1

                return block.buildStatus

        except StopIteration:
            return BuildStatus.end

    def fastForward(self):
        for block in self.iterBlocks():
            self.doTheRunning(block)

    def iterBlocks(self):
        while True:
            if self.nextStep >= len(self.blocks):
                return

            block = self.blocks[self.nextStep]

            if not block.active:
                self.nextStep += 1
                continue

            # TODO: find a better way for breakpoint
            if hasattr(block, "breakPoint"):
                return

            self.nextStep += 1
            yield block

    def doTheRunning(self, block):
        for key, val in self.attrs.iteritems():
            block.setRunTimeAttr(key, val)

        block.execute()

        if block in self.resultAttrMap:
            key = self.resultAttrMap[block]
            node, attr = self.resultAttrs[key]
            self.results[key] = getattr(node, attr)




class GenericBuilder(Builder):
    pass
    fixedAttrs = ()


class Block(object):
    def __init__(self):
        self.uuid = None
        self.notes = ''
        self.attrs = {}
        self.runTimeAttrs = {}
        self._results = None
        self._name = None
        self.log = ''
        self.active = True
        self.parent = None
        self.buildStatus = BuildStatus.nothing


    def setAttr(self, key, typeVal):
        self.attrs[key] = typeVal

    def setRunTimeAttr(self, key, typeVal):
        self.runTimeAttrs[key] = typeVal[1]

    def execute(self):
        try:
            self.ingestInputs()
            self.ingestAttrs()
            log.debug("{0}: start running...".format(self.name))
            stime = time.time()
            self._execute()
            etime = time.time()
            log.info("{0}: finished in {1} s".format(self.name, round(etime - stime,2)))
            self.buildStatus = BuildStatus.success
        except Exception:
            traceStr = '\n'.join(traceback.format_exception(*sys.exc_info()))
            print traceStr
            self.buildStatus = BuildStatus.fail

    @property
    def name(self):
        return self._name or '{0}_{1}'.format(self.__class__.__name__, str(uuid.uuid4()))

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def results(self):
        return self._results

    @results.setter
    def results(self, results):
        self._results = results

    def ingestInputs(self):
        for attrName, typeVal in self.attrs.items():
            attrType, attrVal = typeVal

            if attrType == attr_type.Input:
                nodeName, attr = attrVal

                try:
                    node = next(bl for bl in self.parent.blocks if bl.name == nodeName)
                except StopIteration:
                    raise ValueError("cannot find input block name: {}".format(nodeName))

                try:
                    self.runTimeAttrs[attrName] = getattr(node, attr)
                except AttributeError:
                    raise ValueError("cannot find attribute {} from input block {}".format(attr, node.name))

    def ingestAttrs(self):
        for key, typeVal in self.attrs.iteritems():
            attrType, attrVal = typeVal

            if attrType == attr_type.Input:
                # Input type attrs are ingested in separated method.
                continue

            self.runTimeAttrs[key] = typeVal[1]

    def setNotes(self, notes):
        self.notes = notes

    def dump(self):
        data = OrderedDict()
        data['type'] = self.__class__.__name__
        data['name'] = self.name
        data['notes'] = self.notes

        data['active'] = self.active

        # serialize attrs
        srAttrs = OrderedDict()
        for attrName, val in self.attrs.items():
            attrType, attrVal = str(val[0].__name__), val[1]
            srAttrs[attrName] =(attrType, attrVal)

        data['attrs'] = srAttrs

        return data

    @classmethod
    def load(cls, data):
        blockClass = lib.getBlockClassByName(data.get('type'))

        block = blockClass()
        block.name = data.get('name')
        block.notes = data.get('notes')

        convertedAttrs = OrderedDict()

        for attrName, typeVal in data.get('attrs').items():
            # for old format compatibility with no attrType stored
            # can be removed in the future when all the blueprints have been updated to have attrType
            if not isinstance(typeVal, (list, tuple)):
                attrType = attr_type.guessNameFromValue(typeVal)
                typeVal = (attrType, typeVal)
            ########################################################################################

            attrType = attr_type.getTypeFromName(typeVal[0])
            convertedAttrs[attrName] = (attrType, typeVal[1])

        block.attrs = convertedAttrs
        block.active = data.get('active')
        return block

    def __hash__(self):
        return hash(self.name)

    def isValid(self):
        # TODO: implement this
        pass

    @classmethod
    def isValidClass(cls):
        return all([hasattr(cls, '_execute'), hasattr(cls, 'category')])

    def reload(self, data):
        for attrName, typeVal in data.items():
            if hasattr(self, attrName):
                setattr(self, attrName, typeVal)


    def reset(self):
        self.buildStatus = BuildStatus.nothing
        self.runTimeAttrs = {}
        self.log = ''



class Generic(Block):
    category = 'Generic'
    categoryOrder = 100


class Helper(Block):
    category = 'Helper'
    categoryOrder = 400

class Custom(Block):
    category = 'Custom'
    categoryOrder = 500
