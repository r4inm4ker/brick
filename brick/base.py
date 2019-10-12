import json
from collections import OrderedDict
from lib.path import Path
from .constants import BuildStatus, BLUEPRINT_EXTENSION
from . import attrtype
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
        self.attrs = OrderedDict()
        self.resultAttrs = {}
        # TODO: inspect whether self.resultAttrMap and self.results are required for now.
        self.resultAttrMap = {}
        self.results = {}
        self.nextStep = 0

    @property
    def name(self):
        return self.attrs.get('name', '{0}_{1}'.format(self.__class__.__name__, str(uuid.uuid4())))

    @name.setter
    def name(self, name):
        self.attrs['name'] = name

    def addBlock(self, block):
        self.blocks.append(block)
        block.parent = self

    def saveBlueprint(self, bluePrint, notes=""):

        writeData = OrderedDict()

        writeData['notes'] = notes
        writeData['type'] = self.__class__.__name__
        writeData['attrs'] = self.attrs

        blocks = []

        for op in self.blocks:
            blocks.append(op.dump())

        writeData['blocks'] = blocks

        res = {}
        for resultAttr, (input, attr) in self.resultAttrs.iteritems():
            res[resultAttr] = (input.name, attr)
        writeData['results'] = res

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

    def setAttr(self, key, val):
        self.attrs[key] = val

    def connectResult(self, key, node, attr):
        self.resultAttrs[key] = (node.name, attr)
        self.resultAttrMap[node.name] = key

    @classmethod
    def load(cls, data):
        builderCls = lib.getBuilderClassesByName(data.get('type'))

        builder = builderCls()

        builder.attrs = data.get('attrs')

        for blockData in data.get('blocks'):
            block = Block.load(blockData)
            builder.addBlock(block)

        return builder

    def reset(self):
        self.nextStep = 0
        for op in self.blocks:
            op.reset()

    def reorderOps(self, order):
        nameMap = {op.name: op for op in self.blocks}

        newList = [nameMap.get(name, None) for name in order if nameMap.get(name, None)]

        self.blocks = newList

    def rewind(self):
        self.nextStep = 0

    def buildNext(self):
        try:
            block = next(self.genBlock())

            if block:
                self.doTheRunning(block)

                if block.buildStatus == BuildStatus.fail:
                    self.nextStep -= 1

                return block.buildStatus

        except StopIteration:
            return BuildStatus.end

    def fastForward(self):
        for block in self.genBlock():
            self.doTheRunning(block)

    def genBlock(self):
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
            try:
                node, attr = self.resultAttrs[key]
                self.results[key] = getattr(node, attr)
            except AttributeError:
                log.warn('invalid result attribute: {0}.{1}'.format(node, attr))


class GenericBuilder(Builder):
    pass
    # fixedAttrs = (('variant', (attrtype.Variant, None)),)
    fixedAttrs = ()


class Block(object):
    def __init__(self):
        self.notes = ''
        self.attrs = {}
        self.runTimeAttrs = {}
        self._results = None
        self._name = None
        self.inputs = {}
        self.log = ''
        self.active = True
        self.parent = None
        self.buildStatus = BuildStatus.nothing

    def setAttr(self, key, val):
        self.attrs[key] = val

    def setRunTimeAttr(self, key, val):
        self.runTimeAttrs[key] = val

    def execute(self):
        try:
            self.ingestInputs()
            self.ingestAttrs()
            log.info("{0}: start running...".format(self._name))
            stime = time.time()
            self._execute()
            etime = time.time()
            log.info("{0}: finished. consumed {1} s".format(self._name, etime - stime))
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

    def setInput(self, key, node, attr):
        self.inputs.update({key: (node.name, attr)})

    def ingestInputs(self):
        for key, (nodeName, attr) in self.inputs.iteritems():
            try:
                node = next(bl for bl in self.parent.blocks if bl.name == nodeName)
            except StopIteration:
                continue

            self.runTimeAttrs[key] = getattr(node, attr)

    def ingestAttrs(self):
        for key, val in self.attrs.iteritems():
            self.runTimeAttrs[key] = val

    def setNotes(self, notes):
        self.notes = notes

    def dump(self):
        data = OrderedDict()
        data['type'] = self.__class__.__name__
        data['name'] = self.name
        data['notes'] = self.notes

        inputDict = OrderedDict()
        for key, (nodeName, attr) in self.inputs.iteritems():
            inputDict[key] = attrtype.Input((nodeName, attr))

        data['active'] = self.active
        data['inputs'] = inputDict
        data['attrs'] = self.attrs

        return data

    @classmethod
    def load(cls, data):
        blockClass = lib.getBlockClassByName(data.get('type'))

        block = blockClass()
        block.name = data.get('name')
        block.notes = data.get('notes')
        block.attrs = data.get('attrs')
        block.inputs = data.get('inputs')
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
        self.name = data.get('name')
        self.notes = data.get('notes')
        self.attrs = data.get('attrs')
        self.inputs = data.get('inputs',{})
        self.active = data.get('active',True)

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
