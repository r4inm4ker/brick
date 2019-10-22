import sys
import re
import json
import os
from collections import OrderedDict
from functools import partial
from qqt import QtCore, QtGui, QtWidgets, QtCompat
from qqt.gui import qcreate, VBoxLayout, HBoxLayout, Button, ContextMenu, Splitter, Spacer, StringField

from brick import base
from brick.base import log

from brick import lib
from brick import settings
from brick.constants import BuildStatus

from brick.ui import attrField
from brick.ui import saveLoadBlueprintDialog as ioDialog
from brick.ui.components import block_widgets

from brick.ui import IconManager


def getMainWindow(widget):
    """ get brick window object from child

    :param widget: child widget
    :return: BrickWindow object or None
    """
    currParent = widget
    while True:
        if not currParent:
            return None

        elif isinstance(currParent, BrickWindow):
            return currParent

        else:
            currParent = currParent.parentWidget()


class BrickWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(BrickWindow, self).__init__(parent=parent)
        mainWidget = BrickWidget(mainWindow=self)
        self.currentBlueprint = None
        mainWidget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(mainWidget)
        self.menuBar = None
        self._initMenuBar()
        self._initToolBar()
        self._initPropertyDock()
        self._initLogDock()

        icon = IconManager.get("brick.png", type="icon")
        self.setWindowIcon(icon)

        self.updateTitle()

        self.resize(1300,1080)

    @property
    def mainWidget(self):
        return self.centralWidget()

    @property
    def blueprintWidget(self):
        return self.mainWidget.blueprintWidget

    @property
    def headerWidget(self):
        return self.blueprintWidget.headerWidget

    @property
    def blockListWidget(self):
        return self.blueprintWidget.blockListWidget

    @property
    def builder(self):
        return self.blueprintWidget.builder

    @classmethod
    def launch(cls):
        bui = cls()
        bui.show()
        return bui

    def updateTitle(self, dirty=False):
        baseTitle = "Brick ( {path} )"
        if self.currentBlueprint:
            title = baseTitle.format(path=self.currentBlueprint)
        else:
            title = baseTitle.format(path="Untitled")

        if dirty:
            title = title + "*"

        self.setWindowTitle(title)

    def _initPropertyDock(self):
        self.editorDock = Editor_Dock()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.editorDock)
        self.editorWidget = self.editorDock.mainWidget

        self.blockListWidget.itemSelectionChanged.connect(self.updateEditorWidget)

    def _initLogDock(self):
        self.logDock = Log_Dock()
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.logDock)

    def updateEditorWidget(self):
        items = self.blockListWidget.selectedItems()

        if items:
            widget = items[0].widget
            self.editorWidget.update(widget)
        else:
            self.editorWidget.clear()

    def _initMenuBar(self):
        self.menuBar = QtWidgets.QMenuBar()

        menuFile = QtWidgets.QMenu('File', self.menuBar)
        self.menuBar.addMenu(menuFile)

        action = QtWidgets.QAction('new', self)
        action.triggered.connect(self.newBlueprintCalled)
        menuFile.addAction(action)

        action = QtWidgets.QAction('open...', self)
        action.triggered.connect(self.loadBlueprintDialogCalled)
        menuFile.addAction(action)

        action = QtWidgets.QAction('save...', self)
        action.triggered.connect(self.saveExistingBlueprintCalled)
        menuFile.addAction(action)

        action = QtWidgets.QAction('save as...', self)
        action.triggered.connect(self.saveBlueprintDialogCalled)
        menuFile.addAction(action)

        self.recentMenu = QtWidgets.QMenu('recent blueprints', self.menuBar)
        menuFile.addMenu(self.recentMenu)

        menuWindow = QtWidgets.QMenu('Help', self.menuBar)
        self.menuBar.addMenu(menuWindow)

        action = QtWidgets.QAction('show help', self)
        action.setEnabled(False)
        menuWindow.addAction(action)

        action = QtWidgets.QAction('About', self)
        action.triggered.connect(self.showAboutDialog)
        menuWindow.addAction(action)

        self.setMenuBar(self.menuBar)

        self.updateRecentFileMenu()

    def _initToolBar(self):
        toolBar = QtWidgets.QToolBar(self)

        icon = IconManager.get("new.png", type="icon")
        action = toolBar.addAction(icon, "new blueprint")
        action.triggered.connect(self.newBlueprintCalled)

        icon = IconManager.get("open.png", type="icon")
        action = toolBar.addAction(icon, "open blueprint")
        action.triggered.connect(self.loadBlueprintDialogCalled)

        icon = IconManager.get("save.png", type="icon")
        action = toolBar.addAction(icon, "save blueprint")
        action.triggered.connect(self.saveExistingBlueprintCalled)

        self.addToolBar(toolBar)

    def showAboutDialog(self):
        from brick.ui.components.about import About_Dialog
        dialog = About_Dialog(self)
        dialog.exec_()

    def updateRecentFileMenu(self):
        data = settings.getHistoryData()
        recentBluePrints = data.get(settings.Settings.Recent_Files, [])
        if recentBluePrints:
            self.recentMenu.clear()
            for filePath in recentBluePrints:
                action = QtWidgets.QAction(filePath, self)
                action.triggered.connect(partial(self.loadBluePrint, filePath))
                self.recentMenu.addAction(action)

    def loadBluePrint(self, filePath):
        self.blueprintWidget.load(filePath)
        settings.addRecentBlueprint(filePath)
        self.updateRecentFileMenu()
        self.blockListWidget.scrollToTop()
        self.currentBlueprint = filePath
        self.updateTitle()

    def saveBluePrint(self, data):
        filePath, notes = data
        self.blueprintWidget.builder.saveBlueprint(filePath, notes)
        self.currentBlueprint = filePath
        log.info("Blueprint saved : {}".format(filePath))
        self.updateTitle()

    def saveExistingBlueprintCalled(self):
        if not self.currentBlueprint:
            self.saveBlueprintDialogCalled()
        else:
            confirm = QtWidgets.QMessageBox.question(None,
                                                     'Message',
                                                     "Overwrite {} ?".format(self.currentBlueprint),
                                                     QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                                     QtWidgets.QMessageBox.No)

            if confirm == QtWidgets.QMessageBox.No:
                self.saveBlueprintDialogCalled()
            elif confirm == QtWidgets.QMessageBox.Save:
                with open(self.currentBlueprint, 'r') as fd:
                    data = json.load(fd, object_pairs_hook=OrderedDict)
                    notes = data.get("notes")
                self.saveBluePrint((self.currentBlueprint, notes))

    def saveBlueprintDialogCalled(self):
        ui = ioDialog.SaveBlueprintDialog(self)
        ui.setting_file_updated_signal.connect(self.updateRecentFileMenu)
        ui.saveSignalled.connect(self.saveBluePrint)
        ui.exec_()

    def loadBlueprintDialogCalled(self):
        ui = ioDialog.LoadBlueprintDialog(self)
        ui.setting_file_updated_signal.connect(self.updateRecentFileMenu)
        ui.load_signal.connect(self.loadBluePrint)
        ui.exec_()

    def newBlueprintCalled(self):
        confirm = QtWidgets.QMessageBox.question(None,
                                                 'Message',
                                                 "save current blueprint?",
                                                 QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                                 QtWidgets.QMessageBox.No)

        if confirm == QtWidgets.QMessageBox.No:
            self.clear()
        elif confirm == QtWidgets.QMessageBox.Save:
            self.saveBlueprintDialogCalled()
            self.clear()


    def clear(self):
        self.editorWidget.clear()
        self.blueprintWidget.initDefault()

    def closeEvent(self, *args, **kwargs):

        # disable confirmation window for faster debugging
        ###########
        '''
        confirm = QtWidgets.QMessageBox.question(None,
                                                 'Message',
                                                 "save current blueprint?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                                 QtWidgets.QMessageBox.No)
        if confirm == QtWidgets.QMessageBox.No:
            super(BrickWindow, self).closeEvent(*args, **kwargs)
        elif confirm == QtWidgets.QMessageBox.Yes:
            self.saveBlueprintDialogCalled()
            super(BrickWindow, self).closeEvent(*args, **kwargs)
        '''
        #############

        super(BrickWindow, self).closeEvent(*args, **kwargs)


class BrickWidget(QtWidgets.QWidget):
    def __init__(self, mainWindow=None, parent=None):
        super(BrickWidget, self).__init__(parent=parent)
        self.mainWindow = mainWindow
        self.blueprintWidget = None
        self._initUI()

    def _initUI(self):
        layout = VBoxLayout(self)
        with layout:
            self.hsplitter = qcreate(Splitter)
            with self.hsplitter:
                # left
                self.blockMenuWidget = qcreate(QtWidgets.QWidget, layoutType=VBoxLayout)
                self.blockMenuWidget.setMaximumWidth(200)
                self.blockMenuLayout = self.blockMenuWidget.layout()
                self._populateBlocks()

                # right
                self.blueprintWidget = qcreate(BlueprintWidget)
            self.hsplitter.setSizes([1, 100])

    def _populateBlocks(self):
        blockMap = lib.collectBlocksByCategory()

        with self.blockMenuLayout:
            qcreate(Spacer, mode="vertical")
            for category, blockClasses in blockMap.items():
                gbox = qcreate(QtWidgets.QGroupBox, layoutType=VBoxLayout)
                gbox.setTitle(category)
                with gbox.layout():
                    lwidget = qcreate(BlockMenuListWidget)
                    for blockClass in blockClasses:
                        icon = IconManager.get(blockClass.ui_icon_name, type="icon")
                        item = QtWidgets.QListWidgetItem(icon, blockClass.__name__)
                        item.blockClass = blockClass
                        item.setSizeHint(QtCore.QSize(100, 30))
                        lwidget.addItem(item)
            qcreate(Spacer, mode="vertical")


class BlockMenuListWidget(QtWidgets.QListWidget):
    def __init__(self, *args, **kwargs):
        super(BlockMenuListWidget, self).__init__(*args, **kwargs)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DragOnly)
        self.setSelectionMode(self.ExtendedSelection)

    def mousePressEvent(self, event, *args, **kwargs):
        mainWindow = getMainWindow(self)
        widget = mainWindow.blockListWidget
        mainWindow.blockListWidget.setDragDropMode(widget.DragDrop)
        return super(BlockMenuListWidget, self).mousePressEvent(event)

    def mimeData(self, items):
        data = super(BlockMenuListWidget, self).mimeData(items)

        urls = []
        for item in items:
            className = item.blockClass.__name__
            urls.append(className)

        data.setUrls(urls)

        return data


class BlueprintWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlueprintWidget, self).__init__(parent=parent)
        self._builder = None
        self._initUI()
        self._connectSignals()

    def _initUI(self):
        self.setContentsMargins(0, 0, 0, 0)
        layout = VBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        with layout:
            splitter = qcreate(Splitter, mode="vertical")
            with splitter:
                self.headerWidget = qcreate(HeaderWidget)
                # self.blockMenu = qcreate(BlockMenuWidget,self)

                w2 = qcreate(QtWidgets.QGroupBox, layoutType=VBoxLayout)
                w2.setTitle("Blueprint")
                w2.setStyleSheet('''QGroupBox{ font-size: 14px; font-weight: bold;}''')
                w2.setAlignment(QtCore.Qt.AlignCenter)
                w2.layout().setContentsMargins(0, 0, 0, 0)
                with w2.layout():
                    self.blockListWidget = qcreate(BlockListWidget, blueprintWidget=self)
                    with qcreate(HBoxLayout):
                        icon = IconManager.get("rewind.png", type="icon")
                        self.rewindButton = qcreate(Button, icon, "")
                        self.rewindButton.setMinimumHeight(25)

                        icon = IconManager.get("step_back.png", type="icon")
                        self.stepBackButton = qcreate(Button, icon, "")
                        self.stepBackButton.setMinimumHeight(25)
                        self.stepBackButton.setMaximumWidth(30)

                        icon = IconManager.get("build_next.png", type="icon")
                        self.buildNextButton = qcreate(Button, icon, "")
                        self.buildNextButton.setMinimumHeight(25)

                        icon = IconManager.get("step_forward.png", type="icon")
                        self.stepForwardButton = qcreate(Button, icon, "")
                        self.stepForwardButton.setMinimumHeight(25)
                        self.stepForwardButton.setMaximumWidth(30)

                        icon = IconManager.get("fast_forward.png", type="icon")
                        self.fastForwardButton = qcreate(Button, icon, "")
                        self.fastForwardButton.setMinimumHeight(25)
            splitter.setSizes((50,600))



    def _connectSignals(self):
        self.rewindButton.clicked.connect(self.rewind)
        self.fastForwardButton.clicked.connect(self.fastForward)
        self.buildNextButton.clicked.connect(self.buildNext)

        self.stepBackButton.clicked.connect(self.stepBack)
        self.stepForwardButton.clicked.connect(self.stepForward)

        self.blockListWidget.currentItemChanged.connect(self.refreshIndicator)

        self.blockListWidget.itemOrderChanged.connect(self.itemOrderChanged)
        self.blockListWidget.currentIndexSet.connect(self.setBuilderIndex)

    @property
    def builder(self):
        if not self._builder:
            self._builder = self._createBuilder()
        return self._builder

    @builder.setter
    def builder(self, builder):
        self._builder = builder

    def _createBuilder(self):
        builder = base.GenericBuilder()
        for idx in range(self.headerWidget.attrTree.topLevelItemCount()):
            item = self.headerWidget.attrTree.topLevelItem(idx)
            name = item.getName()
            value = item.getValue()
            builder.attrs[name] = value
        return builder

    def refreshIndicator(self):
        for idx, widget in enumerate(self.blockListWidget.blockWidgets):
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

    def setBuilderIndex(self, index):
        self.builder.nextStep = index
        self.refreshIndicator()

    def syncBuilder(self):
        self.refreshHeaderAttrs()
        blockOrders = [wg.block.name for wg in self.blockListWidget.blockWidgets]

        self.builder.syncOrder(blockOrders)

    def itemOrderChanged(self):
        self.syncBuilder()
        self.refreshIndicator()

    @property
    def nextStep(self):
        try:
            nextStep = self.builder.nextStep
        except AttributeError:
            if not self.blockListWidget.blockWidgets:
                return
            else:
                nextStep = 0

        return nextStep

    @property
    def nextWidget(self):
        for idx, widget in enumerate(self.blockListWidget.blockWidgets):
            if idx == self.nextStep:
                return widget

    def rewind(self):
        self.builder.reset()
        self.refreshIndicator()
        self.blockListWidget.scrollToTop()

    def stepBack(self):
        if self.builder.nextStep > 0:
            self.builder.nextStep -= 1
        self.refreshIndicator()

    def stepForward(self):
        if self.builder.nextStep < len(self.blockListWidget.blockWidgets):
            self.builder.nextStep += 1
        self.refreshIndicator()

    def refreshHeaderAttrs(self):
        mainWindow = getMainWindow(self)
        headerWidget = mainWindow.headerWidget
        headerWidget.syncData()

    def buildNext(self):
        ret = self.builder.buildNext()
        self.refreshIndicator()
        if self.nextWidget:
            self.blockListWidget.setCurrentItem(self.nextWidget.item)

        return ret

    def fastForward(self):
        progressDialog = QtWidgets.QProgressDialog("Running...", "Abort", 0, 100, self)
        progressDialog.show()
        progress = 0

        while True:
            ret = self.buildNext()
            progress += 1
            progressDialog.setValue(progress)
            if ret == BuildStatus.fail or ret == BuildStatus.end:
                break

        progressDialog.setValue(100)

    def load(self, blueprintPath):
        self.clear()
        builder = base.GenericBuilder.loadBlueprint(blueprintPath)
        self.headerWidget.loadAttrs(builder)
        for block in builder.blocks:
            self.insertBlock(block)

        self.builder = builder

    def clear(self):
        self.headerWidget.clear()
        self.blockListWidget.clear()
        self.builder = None

    def initDefault(self):
        self.clear()
        self.builder = None

    def insertBlock(self, block, index=-1):
        self.blockListWidget.insertBlock(block, index=index)
        log.debug("added: {0}".format(self.builder.blocks))

    def addBlock(self, block):
        return self.insertBlock(block)

    def runItemCallback(self, item):
        index = self.blockListWidget.indexFromItem(item).row()
        self.setBuilderIndex(index)
        self.buildNext()


class BlockListWidget(QtWidgets.QListWidget):
    stylesheet = """
    QListView::item {margin:0px;
    selection-background-color: rgb(60,60,60)};
    }
    """

    itemOrderChanged = QtCore.Signal()
    currentIndexSet = QtCore.Signal(int)

    def __init__(self, parent=None, blueprintWidget=None):
        super(BlockListWidget, self).__init__(parent=parent)
        self.blueprintWidget = blueprintWidget
        self.setDragDropMode(self.InternalMove)
        # self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)

        self.setStyleSheet(self.stylesheet)
        self.setAlternatingRowColors(True)

        self.contextMenu = ContextMenu(self)

        # self.contextMenu.addCommand("edit annotation", self.editAnnotationCallback)
        # self.contextMenu.addSeparator()
        icon = IconManager.get("start_from_here.png", type="icon")
        self.contextMenu.addCommand("start from here", self.setNextToSelected, icon=icon)

        self._currItemRow = None

    @property
    def builder(self):
        return self.blueprintWidget.builder

    @property
    def blockWidgets(self):
        return [self.item(idx).widget for idx in range(self.count())]

    def mousePressEvent(self, event, *args, **kwargs):
        self.setDragDropMode(self.InternalMove)
        super(BlockListWidget, self).mousePressEvent(event)

        btn = event.button()
        if btn == QtCore.Qt.MiddleButton or btn == QtCore.Qt.LeftButton:
            self._currItemRow = self.currentRow()

    def mouseMoveEvent(self, event):
        super(BlockListWidget, self).mouseMoveEvent(event)

        newRow = self.currentRow()
        if newRow != self._currItemRow:
            self._currItemRow = newRow

    def rowsInserted(self, *args, **kwargs):
        super(BlockListWidget, self).rowsInserted(*args, **kwargs)
        self.scrollToBottom()

    def setNextToSelected(self):
        index = self.currentIndex()
        self.currentIndexSet.emit(index)

    def editAnnotationCallback(self):
        pass

    def currentIndex(self):
        indices = self.selectedIndexes()
        if indices:
            return indices[0].row()

    def dropEvent(self, event):

        data = event.mimeData()

        source = event.source()
        if isinstance(source, BlockListWidget):
            # self.setDragDropMode(self.InternalMove)
            ret = super(BlockListWidget, self).dropEvent(event)
            self.itemOrderChanged.emit()
            return ret

        elif isinstance(source, BlockMenuListWidget):
            # DIRTY TRICK TO GET WHERE THE NEW ITEM SHOULD BE INSERTED
            # use default behaviour of dropevent to put the item
            super(BlockListWidget, self).dropEvent(event)
            idx = 0
            insertIndex = -1
            while idx < self.count():
                item = self.item(idx)
                if not hasattr(item, "widget"):
                    insertIndex = idx
                    self.takeItem(idx)
                    break

                idx += 1
            #########################################

            blockTypes = [each.path() for each in data.urls()]
            for blockType in blockTypes:
                block = self.blueprintWidget.builder.createBlock(blockType)
                self.insertBlock(block, index=insertIndex)

    def allItems(self):
        return [self.item(idx) for idx in range(self.count())]

    def addBlock(self, block):
        index = self.count()
        self.insertBlock(block, index)

    def insertBlock(self, block, index=-1):
        if index < 0:
            index = self.count()

        item = BlockItem()
        if block.__class__.__name__ == 'BreakPoint':
            item.setSizeHint(QtCore.QSize(50, 40))
            opWidget = block_widgets.BreakPointWidget(block, item)
        else:
            item.setSizeHint(QtCore.QSize(50, 80))
            opWidget = block_widgets.BlockWidget(block, item)
            opWidget.runBlockSignal.connect(self.runBlockCallback)
        opWidget.itemDeleted.connect(self.deleteBlock)
        item.widget, opWidget.item = opWidget, item


        mainWindow = getMainWindow(self)
        opWidget.nameEdited.connect(mainWindow.editorDock.setWindowTitle)

        self.insertItem(index, item)
        self.builder.insertBlock(block, index=index)
        self.setItemWidget(item, opWidget)
        self.clearSelection()
        item.setSelected(True)
        self.itemOrderChanged.emit()

    def runBlockCallback(self, blockWidget):
        item = blockWidget.item
        index = self.indexFromItem(item).row()
        self.blueprintWidget.setBuilderIndex(index)
        self.blueprintWidget.buildNext()

    def deleteBlock(self, block):
        self.builder.blocks.remove(block)
        self.blueprintWidget.syncBuilder()
        log.debug("deleted: {0}".format(self.builder.blocks))



class BlockItem(QtWidgets.QListWidgetItem):
    pass


class HeaderWidget(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(HeaderWidget, self).__init__(parent=parent)
        # self.setFixedHeight(120)
        self.setContentsMargins(0, 0, 0, 0)
        self.setTitle("Global Attributes")
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet('''QGroupBox{ font-size: 12px; font-weight: bold;}''')
        layout = VBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        with layout:
            self.attrTree = qcreate(AttrTree)
            self.attrTree.attrEdited.connect(self.syncData)

    def getData(self):
        data = OrderedDict()
        for idx in range(self.attrTree.topLevelItemCount()):
            item = self.attrTree.topLevelItem(idx)
            name = item.getName()
            attrType = item.attrType
            value = item.getValue()
            data[name] = (attrType, value)

        return data


    def syncData(self):
        data = self.getData()
        mainWindow = getMainWindow(self)
        mainWindow.builder.syncGlobalAttrs(data)

    def initAttrs(self, builder):
        if not hasattr(builder, 'attrs') or not getattr(builder, 'attrs'):
            for attrData in builder.fixedAttrs:
                self.attrTree.addAttr(attrData)
                # self.attrTree.attrEdited.connect(self.syncData)

    def loadAttrs(self, builder):
        for key, typeVal in builder.attrs.items():
            if key not in self.attrTree.attrs():
                attrType, attrVal = typeVal
                # attrType = type(val)
                data = (key, (attrType, attrVal))
                self.attrTree.addAttr(data)
            else:
                attrIndex = self.attrTree.attrs().index(key)
                item = self.attrTree.topLevelItem(attrIndex)
                item.setValue(typeVal)

    def clear(self):
        self.attrTree.clear()

    # # def sizeUp(self):
    # #     numItem = self.attrTree.topLevelItemCount()
    # #     baseHeight = 90
    # #     itemHeight = 30
    # #     self.setFixedHeight(baseHeight + numItem * itemHeight)
    #
    # def reset(self):
    #     self.clear()
    #     self.initAttrs(base.GenericBuilder)


class AttrTree(QtWidgets.QTreeWidget):
    stylesheet = """
    QTreeView {
     border: none;
    }
    """
    _headers = ('attribute', 'value')
    attrEdited = QtCore.Signal()

    def __init__(self, parent=None):
        super(AttrTree, self).__init__(parent=parent)
        self._parent = parent
        self.setColumnCount(len(self._headers))
        self.setHeaderLabels(self._headers)
        self.setStyleSheet(self.stylesheet)
        self.setAlternatingRowColors(True)

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu()

        action = QtWidgets.QAction('add attr', self)
        action.triggered.connect(self.showAddAttrDialog)
        icon = IconManager.get("add.svg", type="icon")
        action.setIcon(icon)
        self.menu.addAction(action)

        action = QtWidgets.QAction('rename attr', self)
        action.triggered.connect(self.renameAttrDialog)
        icon = IconManager.get("edit.svg", type="icon")
        action.setIcon(icon)
        self.menu.addAction(action)

        action = QtWidgets.QAction('remove attr', self)
        action.triggered.connect(self.removeSelectedAttr)
        icon = IconManager.get("trashbin.svg", type="icon")
        action.setIcon(icon)

        self.menu.addAction(action)

        self.menu.exec_(event.globalPos())

    def addAttr(self, attrData):
        attrItem = AttrItem(attrData, parentWidget=self)

        self.addTopLevelItem(attrItem)
        attrItem.setFlags(attrItem.flags() ^ QtCore.Qt.ItemIsSelectable)
        attrItem.setWidget()
        attrItem.signal.attrEdited.connect(self.emitSignal)

        if hasattr(self._parent, "sizeUp"):
            self._parent.sizeUp()

    def emitSignal(self):
        self.attrEdited.emit()

    def setAttr(self, key, val):
        for item in self.allItems():
            if key == item.attrName:
                item.setValue(val)

    def allItems(self):
        items = []
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            items.append(item)

        return items

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
                self.emitSignal()

    def removeAttr(self, attrItem):
        idx = self.indexOfTopLevelItem(attrItem)
        self.takeTopLevelItem(idx)
        log.info('take attribute: {0}'.format(attrItem))

    def renameAttrDialog(self):
        dialog = RenameAttrDialog()
        dialog.renamed_signal.connect(self.renameAttrCallback)
        dialog.exec_()

    def renameAttrCallback(self, newName):
        currItem = self.currentItem()
        currItem.setName(newName)
        self.emitSignal()

    def showAddAttrDialog(self):
        dialog = AddAttrDialog(parent=self)
        dialog.attrAdded.connect(self.attrAddedCallback)
        dialog.exec_()

    def attrAddedCallback(self, data):
        itemData = (data.get("name"), (data.get("type"), data.get("value")))
        self.addAttr(itemData)
        self.emitSignal()

    def attrs(self):
        labels = []
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            labels.append(item.text(0))

        return labels


class ItemEditSignal(QtCore.QObject):
    attrEdited = QtCore.Signal()

class AttrItem(QtWidgets.QTreeWidgetItem):
    # attrEdited = QtCore.Signal()

    def __init__(self, itemData, parentWidget=None):
        super(AttrItem, self).__init__()

        self.signal = ItemEditSignal()

        self.setSizeHint(1, QtCore.QSize(100,30))

        self.parentWidget = parentWidget
        attrName, (attrType, defaultValue) = itemData

        self.attrType = attrType

        self.setText(0, attrName)
        self.setTextAlignment(0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.fieldWidget = attrField.AttrFieldMaker.create(attrType)
        if defaultValue is not None and defaultValue != '':
            self.fieldWidget.setValue(defaultValue)

        # mainWindow = getMainWindow(self.parentWidget)

        # if isinstance(parentWidget, HeaderWidget):

        self.fieldWidget.editFinished.connect(self.emitSignal)

        # self.fieldWidget.editFinished.connect(mainWindow.editorWidget.syncData)
        # self.fieldWidget.editFinished.connect(mainWindow.blueprintWidget.refreshHeaderAttrs)
    def emitSignal(self):
        self.signal.attrEdited.emit()

    @property
    def attrName(self):
        return self.text(0)

    def setWidget(self):
        self.treeWidget().setItemWidget(self, 1, self.fieldWidget)

    def setName(self, name):
        self.setText(0, name)

    def getName(self):
        return self.text(0)

    def getValue(self):
        return self.fieldWidget.getValue()

    def setValue(self, value):
        self.fieldWidget.setValue(value)


class AddAttrDialog(QtWidgets.QDialog):
    title = "Add Attr"
    attrAdded = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super(AddAttrDialog, self).__init__(parent=parent)

        self.setWindowTitle(self.title)
        layout = VBoxLayout(self)
        with layout:
            with qcreate(HBoxLayout):
                qcreate(QtWidgets.QLabel, "Attr Type: ")
                self.fieldWidget = qcreate(attrField.AttrTypeChooser)
            self.attrNameInput = qcreate(StringField, label="Attr Name: ")

            with qcreate(HBoxLayout):
                qcreate(Spacer, mode="horizontal")
                buttonBox = qcreate(QtWidgets.QDialogButtonBox)
                self.addButton = buttonBox.addButton("Add", QtWidgets.QDialogButtonBox.AcceptRole)

        self.addButton.clicked.connect(self._addAttr)

    def _addAttr(self):
        attrName = self.attrNameInput.getValue()

        if not attrName:
            log.warn("please fill the attribute name.")
            return

        attrField = self.fieldWidget.getData()
        attrType = attrField.attrType

        defaultValue = None

        data = {}
        data['name'], data['type'], data['value'] = attrName, attrType, defaultValue
        self.attrAdded.emit(data)
        self.close()


class RenameAttrDialog(QtWidgets.QDialog):
    renamed_signal = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(RenameAttrDialog, self).__init__(*args, **kwargs)
        layout = VBoxLayout(self)
        with layout:
            self.nameField = qcreate(StringField, label="attr name: ")
            self.okBtn = qcreate(Button, "Rename")

        self.okBtn.clicked.connect(self.emitRenameAttr)
        self.nameField.returnPressed.connect(self.emitRenameAttr)

    def emitRenameAttr(self):
        val = self.nameField.getValue()
        self.renamed_signal.emit(val)
        self.close()


class Block_Editor_Widget(QtWidgets.QWidget):
    def __init__(self, blockWidget=None, **kwargs):
        super(Block_Editor_Widget, self).__init__(**kwargs)
        self.blockWidget = blockWidget
        layout = VBoxLayout(self)

    @property
    def block(self):
        return self.blockWidget.block

    def syncData(self):
        data = self.getData()
        if self.blockWidget:
            self.block.reload(data)


    def clear(self):
        layout = self.layout()
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                # looks like it needs this to properly delete the widget?
                widget.deleteLater()
        self.blockWidget = None
        mainWindow = getMainWindow(self)
        mainWindow.editorDock.setWindowTitle("")

    def update(self, blockWidget, force=False):
        mainWindow = getMainWindow(self)

        if blockWidget == self.blockWidget and not force:
            # already on the same block widget, doesn't need to update.
            return

        self.clear()

        mainWindow.editorDock.setWindowTitle(blockWidget.currentName())

        self.blockWidget = blockWidget
        self.blockWidget.editorWidget = self
        self.attrTree = AttrTree(self)
        self.attrTree.attrEdited.connect(self.syncData)
        self.layout().addWidget(self.attrTree)

        block = self.block

        # if not hasattr(block, 'attrs') or not getattr(block, 'attrs'):
        for fixedAttr in self.block.fixedAttrs:
            aname, (atype, aval) = fixedAttr
            self.attrTree.addAttr(fixedAttr)
            if aname in block.attrs:
                typeVal = block.attrs.get(aname)
                self.attrTree.setAttr(aname, typeVal[1])

        for key, typeVal in block.attrs.items():
            if key not in self.attrTree.attrs():
                data = (key, typeVal)
                self.attrTree.addAttr(data)

    def getData(self):
        data = {}
        data['attrs'] = OrderedDict()
        if self.attrTree:
            for idx in range(self.attrTree.topLevelItemCount()):
                item = self.attrTree.topLevelItem(idx)

                name = item.getName()
                value = item.getValue()
                attrType = item.attrType

                data['attrs'][name] = (attrType, value)

        return data


class Editor_Dock(QtWidgets.QDockWidget):
    def __init__(self, *args, **kwargs):
        super(Editor_Dock, self).__init__(*args, **kwargs)
        self.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mainWidget = Block_Editor_Widget()
        self.setWidget(self.mainWidget)
        self.setFloating(False)




class Log_Dock(QtWidgets.QDockWidget):
    def __init__(self, *args, **kwargs):
        super(Log_Dock, self).__init__(*args, **kwargs)
        self.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.setWindowTitle("Output Log")

        if re.match("maya", os.path.basename(sys.executable), re.I):
            from brick.hosts.maya_utils import Maya_Log_Widget
            self.mainWidget = Maya_Log_Widget()
        else:
            from brick.ui.components.log_widget import Log_Widget
            self.mainWidget = Log_Widget()

        self.setWidget(self.mainWidget)
        self.setFloating(False)


def brick_ui():
    ui = BrickWindow.launch()
    return ui
