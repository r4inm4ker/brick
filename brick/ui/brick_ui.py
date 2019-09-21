import os
from collections import OrderedDict
from functools import partial
from Qt import QtCore, QtGui, QtWidgets
from Qt.QtCompat import loadUi
import logging

log = logging.getLogger("brick")

from brick import base
from brick import lib
from brick import attrtype
from brick.constants import BuildStatus
from brick.ui import attrField
from brick.ui import saveLoadBlueprintDialog as ioDialog

from brick.constants import ICON_DIR

UIDIR = os.path.dirname(__file__)


class BrickUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BrickUI, self).__init__(parent=parent)
        self.setWindowTitle("Brick")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        win = BrickWindow()
        layout.addWidget(win)

    @classmethod
    def launch(cls, dockable=False):
        bui = cls()
        bui.show()
        return bui


class BrickWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(BrickWindow, self).__init__(parent=parent)
        self.widget = BrickWidget()
        self.widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.widget)
        self.menuBar = None
        self.initMenuBar()

    def initMenuBar(self):
        self.menuBar = QtWidgets.QMenuBar()

        menuFile = QtWidgets.QMenu('Blueprint', self.menuBar)
        self.menuBar.addMenu(menuFile)

        action = QtWidgets.QAction('new', self)
        action.triggered.connect(self.widget.newBlueprint)
        menuFile.addAction(action)

        action = QtWidgets.QAction('load...', self)
        action.triggered.connect(self.widget.loadBlueprint)
        menuFile.addAction(action)

        action = QtWidgets.QAction('save...', self)
        action.triggered.connect(self.widget.saveBlueprint)
        menuFile.addAction(action)

        menuWindow = QtWidgets.QMenu('Help', self.menuBar)
        self.menuBar.addMenu(menuWindow)

        action = QtWidgets.QAction('show help', self)
        action.setEnabled(False)
        menuWindow.addAction(action)

        self.setMenuBar(self.menuBar)


class BrickWidget(QtWidgets.QWidget):
    _uifile = os.path.join(UIDIR, "brickWidget.ui")

    def __init__(self, parent=None):
        super(BrickWidget, self).__init__(parent=parent)
        loadUi(self._uifile, self)
        self.blueprintWidget = None
        self.initUI()
        self.populateBlocks()

    @classmethod
    def launch(cls):
        mui = cls()
        mui.show()
        return mui

    def initUI(self):
        self.setMinimumHeight(600)
        self.blueprintWidget = BlueprintWidget()
        self.blueprintLayout.addWidget(self.blueprintWidget)
        self.splitter.setSizes([0, 1])

    def populateBlocks(self):
        blockMap = lib.collectBlocksByCategory()

        for category, opclasses in blockMap.items():
            gbox = QtWidgets.QGroupBox()
            layout = QtWidgets.QVBoxLayout()
            gbox.setLayout(layout)
            gbox.setTitle(category)
            self.blockMenuLayout.addWidget(gbox)

            for opcls in opclasses:
                btn = QtWidgets.QPushButton(opcls.__name__)
                layout.addWidget(btn)
                btn.clicked.connect(partial(self.addBlock, opcls.__name__))

    def addBlock(self, opType):
        blockCls = lib.getBlockClassByName(opType)
        op = blockCls()

        nextUniqueName = self.blueprintWidget.getNextUniqueName()
        op.name = nextUniqueName

        self.blueprintWidget.addBlock(op)

    def saveBlueprint(self):
        ui = ioDialog.SaveBlueprintDialog(self)
        ui.exec_()

    def loadBlueprint(self):
        ui = ioDialog.LoadBlueprintDialog(self)
        ui.exec_()

    def newBlueprint(self):
        confirm = QtWidgets.QMessageBox.question(None,
                                             'Message',
                                             "save current blueprint?",
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                             QtWidgets.QMessageBox.No)

        if confirm == QtWidgets.QMessageBox.No:
            self.blueprintWidget.initDefault()
        elif confirm == QtWidgets.QMessageBox.Yes:
            sui = ioDialog.SaveBlueprintDialog(self)
            sui.exec_()

    def closeEvent(self, *args, **kwargs):
        confirm = QtWidgets.QMessageBox.question(None,
                                             'Message',
                                             "save current blueprint?",
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                             QtWidgets.QMessageBox.No)
        if confirm == QtWidgets.QMessageBox.No:
            super(BrickWidget, self).closeEvent(*args, **kwargs)
        elif confirm == QtWidgets.QMessageBox.Yes:
            sui = ioDialog.SaveBlueprintDialog(self)
            sui.exec_()
            super(BrickWidget, self).closeEvent(*args, **kwargs)


class BlueprintWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlueprintWidget, self).__init__(parent=parent)
        self.initUI()
        self.initSignals()
        self.initData()
        self._builder = None

    @property
    def builder(self):
        if not self._builder:
            self._builder = self.createBuilder()
        return self._builder

    @builder.setter
    def builder(self, builder):
        self._builder = builder

    def initUI(self):
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.headerWidget = HeaderWidget()
        layout.addWidget(self.headerWidget)

        self.blockMenu = BlockMenuWidget(self)
        layout.addWidget(self.blockMenu)

        self.itemList = BlockListWidget()
        layout.addWidget(self.itemList)

        horiLayout = QtWidgets.QHBoxLayout()

        self.rewindButton = QtWidgets.QPushButton()
        newicon = os.path.join(UIDIR, 'icons', 'rewind.png')
        icon = QtGui.QIcon(QtGui.QPixmap(newicon))
        self.rewindButton.setIcon(icon)
        self.rewindButton.setMinimumHeight(25)
        horiLayout.addWidget(self.rewindButton)

        self.stepBackButton = QtWidgets.QPushButton()
        newicon = os.path.join(UIDIR, 'icons', 'step_back.png')
        icon = QtGui.QIcon(QtGui.QPixmap(newicon))
        self.stepBackButton.setIcon(icon)
        self.stepBackButton.setMinimumHeight(25)
        self.stepBackButton.setMaximumWidth(30)
        horiLayout.addWidget(self.stepBackButton)

        self.buildNextButton = QtWidgets.QPushButton()
        newicon = os.path.join(UIDIR, 'icons', 'build_next.png')
        icon = QtGui.QIcon(QtGui.QPixmap(newicon))
        self.buildNextButton.setIcon(icon)
        self.buildNextButton.setMinimumHeight(25)
        horiLayout.addWidget(self.buildNextButton)

        self.stepForwardButton = QtWidgets.QPushButton()
        newicon = os.path.join(UIDIR, 'icons', 'step_forward.png')
        icon = QtGui.QIcon(QtGui.QPixmap(newicon))
        self.stepForwardButton.setIcon(icon)
        self.stepForwardButton.setMinimumHeight(25)
        self.stepForwardButton.setMaximumWidth(30)
        horiLayout.addWidget(self.stepForwardButton)

        self.fastForwardButton = QtWidgets.QPushButton()
        newicon = os.path.join(UIDIR, 'icons', 'fast_forward.png')
        icon = QtGui.QIcon(QtGui.QPixmap(newicon))
        self.fastForwardButton.setIcon(icon)
        self.fastForwardButton.setMinimumHeight(25)
        horiLayout.addWidget(self.fastForwardButton)
        layout.addLayout(horiLayout)

    def initSignals(self):
        self.rewindButton.clicked.connect(self.rewind)
        self.fastForwardButton.clicked.connect(self.fastForward)
        self.buildNextButton.clicked.connect(self.buildNext)

        self.stepBackButton.clicked.connect(self.stepBack)
        self.stepForwardButton.clicked.connect(self.stepForward)

        self.itemList.currentItemChanged.connect(self.refreshIndicator)

        self.itemList.itemOrderChanged.connect(self.itemOrderChanged)

    def initData(self):
        self.headerWidget.initAttrs(base.RigBuilder)

    def createBuilder(self):
        builder = base.RigBuilder()

        for idx in range(self.headerWidget.attrTree.topLevelItemCount()):
            item = self.headerWidget.attrTree.topLevelItem(idx)
            name = item.getName()
            value = item.getValue()
            builder.attrs[name] = value

        return builder

    def refreshIndicator(self):
        for idx, widget in enumerate(self.itemList.opWidgets):
            if idx == self.nextStep:
                widget.switchIndicator(BuildStatus.next)
                try:
                    status = self.builder.blocks[idx].buildStatus
                    if status == BuildStatus.fail:
                        widget.switchIndicator(status)
                except (IndexError, AttributeError):
                    return

            else:
                try:
                    status = self.builder.blocks[idx].buildStatus
                    widget.switchIndicator(status)
                except (IndexError, AttributeError):
                    widget.switchIndicator(BuildStatus.nothing)

    def collectItemMap(self):
        return [wg.op.name for wg in self.itemList.opWidgets]

    def itemOrderChanged(self):
        opOrder = self.collectItemMap()
        self.builder.reorderOps(opOrder)
        self.refreshIndicator()

    @property
    def nextStep(self):
        try:
            nextStep = self.builder.nextStep
        except AttributeError:
            if not self.itemList.opWidgets:
                return
            else:
                nextStep = 0

        return nextStep

    @property
    def nextWidget(self):
        for idx, widget in enumerate(self.itemList.opWidgets):
            if idx == self.nextStep:
                return widget

    def refreshAllBlocks(self):
        for opWidget in self.itemList.opWidgets:
            data = opWidget.genData()
            opWidget.op.reload(data)

    def refreshNextBlock(self):
        widget = self.nextWidget
        if widget:
            data = self.nextWidget.genData()
            self.builder.blocks[self.nextStep].reload(data)

    def rewind(self):
        self.builder.reset()
        self.refreshIndicator()
        self.itemList.scrollToTop()

    def stepBack(self):
        if self.builder.nextStep > 0:
            self.builder.nextStep -= 1
        self.refreshIndicator()

    def stepForward(self):
        if self.builder.nextStep < len(self.itemList.opWidgets):
            self.builder.nextStep += 1
        self.refreshIndicator()

    def refreshHeaderAttrs(self):
        self.builder.attrs.clear()
        for idx in range(self.headerWidget.attrTree.topLevelItemCount()):
            item = self.headerWidget.attrTree.topLevelItem(idx)
            name = item.getName()
            value = item.getValue()
            self.builder.attrs[name] = value

    def buildNext(self):
        self.refreshHeaderAttrs()
        self.refreshNextBlock()
        ret = self.builder.buildNext()
        self.refreshIndicator()
        if self.nextWidget:
            self.itemList.setCurrentItem(self.nextWidget.item)

        return ret

    def fastForward(self):
        progressDialog = QtWidgets.QProgressDialog("Running...","Abort",0, 100, self)
        # progressDialog.setWindowModality(QtCore.Qt.WindowModal)
        progressDialog.show()
        #
        #
        # pm.progressWindow(
        #     title='Running...',
        #     status='Running ...',
        #     min=0,
        #     max=100,
        #     isInterruptable=True)
        #
        progress = 0
        #
        # status = "Running ..."

        while True:
            ret = self.buildNext()
            progress += 1
            progressDialog.setValue(progress)
            if ret == BuildStatus.fail or ret == BuildStatus.end:
                break
            # pm.refresh()
            # pm.progressWindow(edit=True, status=status, progress=progress)

        progressDialog.setValue(100)

    def refreshBuilder(self):
        self.refreshHeaderAttrs()
        self.refreshAllBlocks()

    def save(self, blueprintPath, notes=""):
        self.refreshBuilder()
        self.builder.saveBlueprint(blueprintPath, notes=notes)

    def load(self, blueprintPath):
        self.clear()
        builder = base.RigBuilder.loadBlueprint(blueprintPath)
        self.headerWidget.loadAttrs(builder)
        for block in builder.blocks:
            self.addBlock(block)

        self.builder = builder

    def clear(self):
        self.headerWidget.reset()
        self.itemList.clear()
        self.builder = None

    def initDefault(self):
        self.clear()
        self.builder = None

    def getNextUniqueName(self):
        baseName = 'block'
        blockIndex = 1
        while True:
            uname = "{0}{1}".format(baseName, blockIndex)
            for idx in range(self.itemList.count()):
                item = self.itemList.item(idx)
                if not hasattr(item.widget, 'blockName'):
                    continue
                if uname == item.widget.blockName.text():
                    blockIndex += 1
                    repeat = True
                    break
            else:
                repeat = False

            if repeat:
                continue
            else:
                return uname

    def addBlock(self, block):
        item = BlockItem()
        if block.__class__.__name__ == 'BreakPoint':
            item.setSizeHint(QtCore.QSize(50, 60))
            opWidget = BreakpointWidget(block, item)
        else:
            item.setSizeHint(QtCore.QSize(50, 130))
            opWidget = BlockWidget(block, item)

        opWidget.itemDeleted.connect(self.deleteBlock)

        item.widget, opWidget.item = opWidget, item

        self.itemList.addItem(item)
        self.builder.addBlock(block)
        self.itemList.setItemWidget(item, opWidget)
        self.itemList.setCurrentItem(item)

        # TODO: find a more reliable way to do this (init indicator)
        self.refreshIndicator()

        log.info("added: {0}".format(self.builder.blocks))

    def deleteBlock(self, op):
        self.builder.blocks.remove(op)
        log.info("deleted: {0}".format(self.builder.blocks))


class BlockMenuWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlockMenuWidget, self).__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        label = QtWidgets.QLabel("+")
        layout.addWidget(label)

        menuBar = QtWidgets.QMenuBar()

        blockMap = lib.collectBlocksByCategory()

        for category, opclasses in blockMap.items():
            categoryMenu = QtWidgets.QMenu(category, menuBar)
            categoryMenu.setStyleSheet("QMenu {border: 1px solid black;}")
            menuBar.addMenu(categoryMenu)

            for opcls in opclasses:
                action = QtWidgets.QAction(opcls.__name__, self)
                action.triggered.connect(partial(self.addBlockByType, opcls.__name__))
                categoryMenu.addAction(action)

        layout.addWidget(menuBar)

    @property
    def blueprintWidget(self):
        return self.parentWidget()

    def addBlockByType(self, blockType):
        blockCls = lib.getBlockClassByName(blockType)
        op = blockCls()

        nextUniqueName = self.blueprintWidget.getNextUniqueName()
        op.name = nextUniqueName

        self.blueprintWidget.addBlock(op)


class BlockListWidget(QtWidgets.QListWidget):
    stylesheet = """
    QListView::item {margin:0px;
    selection-background-color: rgb(60,60,60)};
    }
    """

    itemOrderChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(BlockListWidget, self).__init__(parent=parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        self.setStyleSheet(self.stylesheet)
        self._currItemRow = None

    @property
    def opWidgets(self):
        return [self.item(idx).widget for idx in range(self.count())]

    def mousePressEvent(self, event, *args, **kwargs):
        super(BlockListWidget, self).mousePressEvent(event)

        btn = event.button()
        if btn == QtCore.Qt.MiddleButton or btn == QtCore.Qt.LeftButton:
            self._currItemRow = self.currentRow()

    def mouseMoveEvent(self, event):
        super(BlockListWidget, self).mouseMoveEvent(event)

        newRow = self.currentRow()
        if newRow != self._currItemRow:
            self.itemOrderChanged.emit()
            self._currItemRow = newRow

    def rowsInserted(self, *args, **kwargs):
        super(BlockListWidget, self).rowsInserted(*args, **kwargs)
        self.scrollToBottom()


class BlockItem(QtWidgets.QListWidgetItem):
    def sizeUp(self):
        pass


class HeaderWidget(QtWidgets.QWidget):
    _uifile = os.path.join(UIDIR, "headerWidget.ui")

    def __init__(self, parent=None):
        super(HeaderWidget, self).__init__(parent=parent)
        self.setFixedHeight(100)
        self.setContentsMargins(0, 0, 0, 0)

        loadUi(self._uifile, self)

        self.attrTree = AttrTree(self)

        self.attrTreeLayout.addWidget(self.attrTree)

    def initAttrs(self, builder):
        if not hasattr(builder, 'attrs') or not getattr(builder, 'attrs'):
            for attrData in builder.fixedAttrs:
                self.attrTree.addAttr(attrData)

    def loadAttrs(self, builder):
        for key, val in builder.attrs.iteritems():
            if key not in self.attrTree.attrs():
                attrType = type(val)
                data = (key, (attrType, val))
                self.attrTree.addAttr(data)
            else:
                attrIndex = self.attrTree.attrs().index(key)
                item = self.attrTree.topLevelItem(attrIndex)
                item.setValue(val)

    def clear(self):
        self.attrTree.clear()

    def sizeUp(self):
        numItem = self.attrTree.topLevelItemCount()
        baseHeight = 90
        itemHeight = 30
        self.setFixedHeight(baseHeight + numItem * itemHeight)

    def reset(self):
        self.clear()
        self.initAttrs(base.RigBuilder)


class BaseBlockWidget(QtWidgets.QWidget):
    itemDeleted = QtCore.Signal(object)

    def __init__(self, op, item, parent=None):
        super(BaseBlockWidget, self).__init__(parent=parent)
        self.op = op
        self.item = item
        self._headerStyleSheet = None

    def createOp(self):
        data = OrderedDict()
        data['type'] = self.op.__class__.__name__
        data['name'] = ""
        data['description'] = ""
        data['attrs'] = {}
        data['inputs'] = {}
        data['active'] = self.activeCheckBox.isChecked()

        return self.op.load(data)

    def initSignals(self):
        self.deleteButton.clicked.connect(self.delete)
        self.activeCheckBox.clicked.connect(self.switchActiveState)

    def delete(self):
        self.itemDeleted.emit(self.op)
        item = self.item
        lw = item.listWidget()
        idx = lw.indexFromItem(item).row()
        lw.takeItem(idx)

    def switchActiveState(self):
        currState = self.activeCheckBox.isChecked()

        if currState:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("""QWidget {background-color:gray;}""")


class BreakpointWidget(BaseBlockWidget):
    _uifile = os.path.join(UIDIR, "breakpoint.ui")

    def __init__(self, op, item, parent=None):
        super(BreakpointWidget, self).__init__(op, item, parent=parent)
        loadUi(self._uifile, self)

        self.setContentsMargins(0, 0, 0, 0)

        self.op = op

        self.initSignals()

    def switchIndicator(self, state):
        return

    def genData(self):
        data = OrderedDict()
        data['type'] = self.op.__class__.__name__
        data['active'] = self.activeCheckBox.isChecked()
        return data


class BlockWidget(BaseBlockWidget):
    _uifile = os.path.join(UIDIR, "blockWidget.ui")

    def __init__(self, op, item, parent=None):
        super(BlockWidget, self).__init__(op, item, parent=parent)
        loadUi(self._uifile, self)

        self.setContentsMargins(0, 0, 0, 0)

        self.op = op

        self.blockType.setText(op.__class__.__name__)

        self.attrTree = AttrTree(self)

        if not hasattr(op, 'attrs') or not getattr(op, 'attrs'):
            for fixedAttr in self.op.fixedAttrs:
                self.attrTree.addAttr(fixedAttr)

        self.attrTreeLayout.addWidget(self.attrTree)

        self.initSignals()
        self.loadData()

    def initSignals(self):
        super(BlockWidget, self).initSignals()
        self.blockName.textEdited.connect(self.editNameChange)

    def editNameChange(self):
        self.op.name = self.blockName.text()

    def loadData(self):
        op = self.op
        self.blockName.setText(op.name)

        for key, val in op.attrs.iteritems():
            if key not in self.attrTree.attrs():
                attrType = type(val)
                data = (key, (attrType, val))
                self.attrTree.addAttr(data)

        for key, val in op.inputs.iteritems():
            if key not in self.attrTree.attrs():
                data = (key, (type(val), val))
                self.attrTree.addAttr(data)

    def genData(self):
        data = OrderedDict()
        data['type'] = self.op.__class__.__name__
        data['name'] = self.blockName.text()
        data['description'] = ""

        attrs = {}
        inputs = {}
        for idx in range(self.attrTree.topLevelItemCount()):
            item = self.attrTree.topLevelItem(idx)

            name = item.getName()
            value = item.getValue()

            if item.attrType == attrtype.Input:

                inputs[name] = value

            else:
                attrs[name] = value

        data['attrs'] = attrs

        data['inputs'] = inputs
        data['active'] = self.activeCheckBox.isChecked()
        return data

    def createOp(self):
        data = self.genData()
        return self.op.load(data)

    def sizeUp(self):
        item = self.item
        numItem = self.attrTree.topLevelItemCount()
        baseHeight = 90
        itemHeight = 30
        sizeHint = QtCore.QSize(item.sizeHint().width(), baseHeight + numItem * itemHeight)

        item.setSizeHint(sizeHint)

    def switchIndicator(self, state):
        self.indicatorWidget.setCurrentIndex(state)


class AttrTree(QtWidgets.QTreeWidget):
    stylesheet = """
    QTreeView {
     border: none;
    }
    """
    _headers = ('attribute', 'value')

    def __init__(self, parent=None):
        super(AttrTree, self).__init__(parent=parent)
        self._parent = parent
        self.setColumnCount(len(self._headers))
        self.setHeaderLabels(self._headers)
        self.setStyleSheet(self.stylesheet)

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu()

        action = QtWidgets.QAction('add attr', self)
        action.triggered.connect(self.showAddAttrDialog)
        self.menu.addAction(action)

        action = QtWidgets.QAction('add input', self)
        action.triggered.connect(self.showAddInputDialog)
        self.menu.addAction(action)

        action = QtWidgets.QAction('remove attr/input', self)
        action.triggered.connect(self.removeSelectedAttr)
        self.menu.addAction(action)

        self.menu.exec_(event.globalPos())

    def addAttr(self, attrData):
        attrItem = AttrItem(attrData)
        self.addTopLevelItem(attrItem)
        attrItem.setFlags(attrItem.flags() ^ QtCore.Qt.ItemIsSelectable)
        attrItem.setWidget()
        self._parent.sizeUp()

    def addInput(self, inputData):
        inputItem = AttrItem(inputData)
        self.addTopLevelItem(inputItem)
        inputItem.setWidget()
        self._parent.sizeUp()

    def removeSelectedAttr(self):
        currItem = self.currentItem()
        if currItem:
            confirm = QtWidgets.QMessageBox.question(None,
                                             'Message',
                                             "delete attribute {0} ?".format(currItem.attrName),
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                             QtWidgets.QMessageBox.No)
            if confirm == QtWidgets.QMessageBox.Yes:
                self.removeAttr(currItem)

    def removeAttr(self, attrItem):
        idx = self.indexOfTopLevelItem(attrItem)
        self.takeTopLevelItem(idx)
        log.info('take attribute: {0}'.format(attrItem))

    def showAddInputDialog(self):
        AddInputDialog(parent=self)

    def showAddAttrDialog(self):
        AddAttrDialog(parent=self)

    def attrs(self):
        labels = []
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            labels.append(item.text(0))

        return labels


class AttrItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, itemData):
        super(AttrItem, self).__init__()

        attrName, (attrType, defaultValue) = itemData

        self.attrType = attrType

        self.setText(0, attrName)
        self.setTextAlignment(0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.fieldWidget = attrField.AttrFieldMaker.create(attrType)
        if defaultValue is not None and defaultValue != '':
            self.fieldWidget.setValue(defaultValue)

    @property
    def attrName(self):
        return self.text(0)

    def setWidget(self):
        self.treeWidget().setItemWidget(self, 1, self.fieldWidget)

    def getName(self):
        return self.text(0)

    def getValue(self):
        return self.fieldWidget.getValue()

    def setValue(self,value):
        self.fieldWidget.setValue(value)


class AddAttrDialog(QtWidgets.QDialog):
    # TODO need refactor
    WINDOW_TITLE = "Add Attr"

    def __init__(self, parent=None):
        super(AddAttrDialog, self).__init__(parent=parent)
        self.__resourceName = ""
        self.initUI()
        self.initSignals()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.WINDOW_TITLE)
        mainLayout = QtWidgets.QVBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()
        nodeNameLayout = QtWidgets.QHBoxLayout()
        tagLayout = QtWidgets.QHBoxLayout()

        buttonBoxSpacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding)

        self.setModal(True)
        buttonBox = QtWidgets.QDialogButtonBox()
        self.__addButton = buttonBox.addButton("Add", QtWidgets.QDialogButtonBox.AcceptRole)
        self.__addButton.setEnabled(True)
        self.__closeButton = buttonBox.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)

        buttonLayout.addItem(buttonBoxSpacer)
        buttonLayout.addWidget(buttonBox)

        inputLabel = QtWidgets.QLabel("Attr Name:")
        self.__attrNameInput = QtWidgets.QLineEdit()

        nodeNameLayout.addWidget(inputLabel)
        nodeNameLayout.addWidget(self.__attrNameInput)

        horLay = QtWidgets.QHBoxLayout()
        mainLayout.addLayout(horLay)
        text = QtWidgets.QLabel('Attr Type: ')
        horLay.addWidget(text)
        self.fieldWidget = attrField.AttrTypeChooser()
        horLay.addWidget(self.fieldWidget)

        mainLayout.addLayout(nodeNameLayout)
        mainLayout.addLayout(tagLayout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def initSignals(self):
        self.__addButton.released.connect(self._addAttr)
        self.__closeButton.released.connect(self.close)

    def _addAttr(self):
        attrName = self.__attrNameInput.text()

        if not attrName:
            log.warn("please fill the attribute name.")
            return

        attrType = self.fieldWidget.getData()

        defaultValue = None

        self.parentWidget().addAttr((attrName, (attrType, defaultValue)))

        self.close()


class AddInputDialog(QtWidgets.QDialog):
    # TODO need refactor
    WINDOW_TITLE = "Add Attr"

    def __init__(self, parent=None):
        super(AddInputDialog, self).__init__(parent=parent)
        self.__resourceName = ""
        self.initUI()
        self.initSignals()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.WINDOW_TITLE)
        mainLayout = QtWidgets.QVBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()
        nodeNameLayout = QtWidgets.QHBoxLayout()
        tagLayout = QtWidgets.QHBoxLayout()

        buttonBoxSpacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding)

        self.setModal(True)
        buttonBox = QtWidgets.QDialogButtonBox()
        self.__addButton = buttonBox.addButton("Add", QtWidgets.QDialogButtonBox.AcceptRole)
        self.__addButton.setEnabled(True)
        self.__closeButton = buttonBox.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)

        buttonLayout.addItem(buttonBoxSpacer)
        buttonLayout.addWidget(buttonBox)

        inputLabel = QtWidgets.QLabel("variable name:")
        self.__attrNameInput = QtWidgets.QLineEdit()

        nodeNameLayout.addWidget(inputLabel)
        nodeNameLayout.addWidget(self.__attrNameInput)

        mainLayout.addLayout(nodeNameLayout)
        mainLayout.addLayout(tagLayout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def initSignals(self):
        self.__addButton.released.connect(self._addAttr)
        self.__closeButton.released.connect(self.close)

    def _addAttr(self):
        attrName = self.__attrNameInput.text()

        if not attrName:
            log.warn("please fill the attribute name.")
            return

        attrType = attrtype.Input
        defaultValue = None
        self.parentWidget().addAttr((attrName, (attrType, defaultValue)))
        self.close()



def ui():
    ui = BrickUI.launch()
    return ui