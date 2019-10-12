import os
from collections import OrderedDict
from functools import partial
from qqt import QtCore, QtGui, QtWidgets, QtCompat
from qqt.gui import qcreate, VBoxLayout, HBoxLayout, Button, ContextMenu, Splitter, Spacer

loadUi = QtCompat.loadUi

import logging

log = logging.getLogger("brick")

from brick import base
from brick import lib
from brick import attrtype
from brick.constants import BuildStatus
from brick.ui import attrField
from brick.ui import saveLoadBlueprintDialog as ioDialog

from brick import settings

from brick.lib.path import Path

from brick.ui import IconManager

UIDIR = os.path.dirname(__file__)


class Main_UI(object):
    ui = None


class BrickUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BrickUI, self).__init__(parent=parent)
        self.setWindowTitle("Brick")
        icon = IconManager.get("brick.png", type="icon")
        self.setWindowIcon(icon)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        win = BrickWindow()
        layout.addWidget(win)
        self.resize(800,1000)


    @classmethod
    def launch(cls):
        bui = cls()
        bui.show()
        return bui


class BrickWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(BrickWindow, self).__init__(parent=parent)
        Main_UI.ui = self
        self.mainWidget = BrickWidget(mainWindow=self)
        self.bluePrintWidget = self.mainWidget.blueprintWidget
        self.blockListWidget = self.bluePrintWidget.blockListWidget
        self.mainWidget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.mainWidget)
        self.menuBar = None
        self._initMenuBar()
        self._initToolBar()
        self._initPropertyDock()

    def _initPropertyDock(self):
        self.editorDock = Editor_Dock()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.editorDock)
        self.editorWidget = self.editorDock.mainWidget

        self.blockListWidget.itemSelectionChanged.connect(self.updateEditorWidget)

    def updateEditorWidget(self):
        # if self.editorWidget.blockWidget:
        #     self.editorWidget.blockWidget.syncData()

        items = self.blockListWidget.selectedItems()

        self.editorWidget.clear()

        if items:
            item = items[0]
            self.editorWidget.update(item.widget)


    def _initMenuBar(self):
        self.menuBar = QtWidgets.QMenuBar()

        menuFile = QtWidgets.QMenu('File', self.menuBar)
        self.menuBar.addMenu(menuFile)

        action = QtWidgets.QAction('new', self)
        action.triggered.connect(self.mainWidget.newBlueprint)
        menuFile.addAction(action)

        action = QtWidgets.QAction('load...', self)
        action.triggered.connect(self.mainWidget.loadBlueprintDialogCalled)
        menuFile.addAction(action)

        action = QtWidgets.QAction('save...', self)
        action.triggered.connect(self.mainWidget.saveBlueprintDialogCalled)
        menuFile.addAction(action)

        self.recentMenu = QtWidgets.QMenu('recent blueprints', self.menuBar)
        menuFile.addMenu(self.recentMenu)

        menuWindow = QtWidgets.QMenu('Help', self.menuBar)
        self.menuBar.addMenu(menuWindow)

        action = QtWidgets.QAction('show help', self)
        action.setEnabled(False)
        menuWindow.addAction(action)

        self.setMenuBar(self.menuBar)

        self.updateRecentFileMenu()

    def updateRecentFileMenu(self):
        data = settings.getHistoryData()
        recentBluePrints = data.get(settings.Settings.Recent_Files,[])
        if recentBluePrints:
            self.recentMenu.clear()
            for filePath in recentBluePrints:
                action = QtWidgets.QAction(filePath,self)
                action.triggered.connect(partial(self.loadBluePrint,filePath))
                self.recentMenu.addAction(action)


    def loadBluePrint(self, filePath):
        self.mainWidget.blueprintWidget.load(filePath)
        settings.addRecentBlueprint(filePath)
        self.updateRecentFileMenu()

    def saveBluePrint(self, (path, notes)):
        # if self.editorWidget.blockWidget:
        #     self.editorWidget.blockWidget.syncData()
        self.mainWidget.blueprintWidget.builder.saveBlueprint(path, notes)

    def _initToolBar(self):
        toolBar = QtWidgets.QToolBar()

        icon = IconManager.get("new.png", type="icon")
        action = toolBar.addAction(icon, "new blueprint")
        action.triggered.connect(self.mainWidget.newBlueprint)

        icon = IconManager.get("open.png", type="icon")
        action = toolBar.addAction(icon, "open blueprint")
        action.triggered.connect(self.mainWidget.loadBlueprintDialogCalled)


        icon = IconManager.get("save.png", type="icon")
        action = toolBar.addAction(icon, "save blueprint")
        action.triggered.connect(self.mainWidget.saveBlueprintDialogCalled)


        self.addToolBar(toolBar)

class BrickWidget(QtWidgets.QWidget):
    def __init__(self, mainWindow=None, parent=None):
        super(BrickWidget, self).__init__(parent=parent)
        self.mainWindow = mainWindow
        self.blueprintWidget = None
        self._initUI()
        # self.populateBlocks()
        self.__test()

    def __test(self):
        pass
        # self.blueprintWidget.load(r"E:\git\brick\brick\test\templates\debug.json")

    def _initUI(self):
        layout = VBoxLayout(self)
        with layout:
            self.hsplitter = qcreate(Splitter)
            with self.hsplitter:
                # left
                self.blockMenuWidget = qcreate(QtWidgets.QWidget,layoutType=VBoxLayout)
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
            for category, opclasses in blockMap.items():
                gbox = qcreate(QtWidgets.QGroupBox, layoutType=VBoxLayout)
                gbox.setTitle(category)
                with gbox.layout():
                    lwidget = qcreate(BlockMenuListWidget)
                    for opcls in opclasses:
                        icon = IconManager.get(opcls.ui_icon_name,type="icon")
                        item = QtWidgets.QListWidgetItem(icon, opcls.__name__)
                        item.opcls = opcls
                        item.setSizeHint(QtCore.QSize(100,30))
                        lwidget.addItem(item)
                        # btn = QtWidgets.QPushButton(opcls.__name__)
                        # layout.addWidget(btn)
                        # btn.clicked.connect(partial(self.addBlock, opcls.__name__))
            qcreate(Spacer, mode="vertical")
            # gbox = QtWidgets.QGroupBox()
            # layout = QtWidgets.QVBoxLayout()
            # gbox.setLayout(layout)
            # gbox.setTitle(category)
            # self.blockMenuLayout.addWidget(gbox)
            #
            # for opcls in opclasses:
            #     btn = QtWidgets.QPushButton(opcls.__name__)
            #     layout.addWidget(btn)
            #     btn.clicked.connect(partial(self.addBlock, opcls.__name__))

    def addBlock(self, opType):
        blockCls = lib.getBlockClassByName(opType)
        op = blockCls()

        nextUniqueName = self.blueprintWidget.getNextUniqueName()
        op.name = nextUniqueName

        self.blueprintWidget.addBlock(op)

    def saveBlueprintDialogCalled(self):
        ui = ioDialog.SaveBlueprintDialog(self)
        ui.setting_file_updated_signal.connect(self.mainWindow.updateRecentFileMenu)
        ui.saveSignalled.connect(self.mainWindow.saveBluePrint)
        ui.exec_()



    def loadBlueprintDialogCalled(self):
        ui = ioDialog.LoadBlueprintDialog(self)

        ui.setting_file_updated_signal.connect(self.mainWindow.updateRecentFileMenu)
        ui.load_signal.connect(self.mainWindow.loadBluePrint)

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


class BlockMenuListWidget(QtWidgets.QListWidget):
    def __init__(self,*args,**kwargs):
        super(BlockMenuListWidget, self).__init__(*args,**kwargs)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DragOnly)
        self.setSelectionMode(self.ExtendedSelection)

    def mousePressEvent(self, event, *args, **kwargs):
        widget = Main_UI.ui.blockListWidget
        Main_UI.ui.blockListWidget.setDragDropMode(widget.DragDrop)

        return super(BlockMenuListWidget, self).mousePressEvent(event)


    def mouseMoveEvent(self, event):



        return super(BlockMenuListWidget, self).mouseMoveEvent(event)



    def mimeData(self, items):
        data = super(BlockMenuListWidget,self).mimeData(items)

        urls = []
        for item in items:
            className = item.opcls.__name__
            urls.append(className)

        data.setUrls(urls)

        return data


class BlueprintWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlueprintWidget, self).__init__(parent=parent)
        self._builder = None
        self._initUI()
        self._connectSignals()
        self._initData()


    @property
    def builder(self):
        if not self._builder:
            self._builder = self.createBuilder()
        return self._builder

    @builder.setter
    def builder(self, builder):
        self._builder = builder

    def _initUI(self):
        self.setContentsMargins(0, 0, 0, 0)
        layout = VBoxLayout(self)
        with layout:
            self.headerWidget = qcreate(HeaderWidget)
            self.blockMenu = qcreate(BlockMenuWidget,self)
            self.blockListWidget = qcreate(BlockListWidget, blueprintWidget=self)
            with qcreate(HBoxLayout):
                icon = IconManager.get("rewind.png", type="icon")
                self.rewindButton = qcreate(Button,icon,"")
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

    def _connectSignals(self):
        self.rewindButton.clicked.connect(self.rewind)
        self.fastForwardButton.clicked.connect(self.fastForward)
        self.buildNextButton.clicked.connect(self.buildNext)

        self.stepBackButton.clicked.connect(self.stepBack)
        self.stepForwardButton.clicked.connect(self.stepForward)

        self.blockListWidget.currentItemChanged.connect(self.refreshIndicator)

        self.blockListWidget.itemOrderChanged.connect(self.itemOrderChanged)
        self.blockListWidget.currentIndexSet.connect(self.setBuilderIndex)

    def _initData(self):
        self.headerWidget.initAttrs(base.GenericBuilder)

    def createBuilder(self):
        builder = base.GenericBuilder()

        for idx in range(self.headerWidget.attrTree.topLevelItemCount()):
            item = self.headerWidget.attrTree.topLevelItem(idx)
            name = item.getName()
            value = item.getValue()
            builder.attrs[name] = value

        return builder

    def refreshIndicator(self):
        for idx, widget in enumerate(self.blockListWidget.opWidgets):
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

    def collectItemMap(self):
        return [wg.op.name for wg in self.blockListWidget.opWidgets]

    def itemOrderChanged(self):
        opOrder = self.collectItemMap()
        self.builder.reorderOps(opOrder)
        self.refreshIndicator()

    @property
    def nextStep(self):
        try:
            nextStep = self.builder.nextStep
        except AttributeError:
            if not self.blockListWidget.opWidgets:
                return
            else:
                nextStep = 0

        return nextStep

    @property
    def nextWidget(self):
        for idx, widget in enumerate(self.blockListWidget.opWidgets):
            if idx == self.nextStep:
                return widget

    # def refreshAllBlocks(self):
        # for opWidget in self.blockListWidget.opWidgets:
        #     data = opWidget.genData()
        #     opWidget.op.reload(data)

    # def refreshNextBlock(self):
    #     widget = self.nextWidget
    #     if widget:
    #         data = self.nextWidget.genData()
    #         self.builder.blocks[self.nextStep].reload(data)

    def rewind(self):
        self.builder.reset()
        self.refreshIndicator()
        self.blockListWidget.scrollToTop()

    def stepBack(self):
        if self.builder.nextStep > 0:
            self.builder.nextStep -= 1
        self.refreshIndicator()

    def stepForward(self):
        if self.builder.nextStep < len(self.blockListWidget.opWidgets):
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
        # self.refreshNextBlock()
        ret = self.builder.buildNext()
        self.refreshIndicator()
        if self.nextWidget:
            self.blockListWidget.setCurrentItem(self.nextWidget.item)

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
        # self.refreshAllBlocks()

    # def save(self, blueprintPath, notes=""):
    #     self.refreshBuilder()
    #     self.builder.saveBlueprint(blueprintPath, notes=notes)

    def load(self, blueprintPath):
        self.clear()
        builder = base.GenericBuilder.loadBlueprint(blueprintPath)
        self.headerWidget.loadAttrs(builder)
        for block in builder.blocks:
            self.insertBlock(block)

        self.builder = builder

    def clear(self):
        self.headerWidget.reset()
        self.blockListWidget.clear()
        self.builder = None

    def initDefault(self):
        self.clear()
        self.builder = None

    def getNextUniqueName(self):
        baseName = 'block'
        blockIndex = 1
        while True:
            uname = "{0}{1}".format(baseName, blockIndex)
            for idx in range(self.blockListWidget.count()):
                item = self.blockListWidget.item(idx)
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

    def insertBlock(self, block, index=-1):
        self.blockListWidget.insertBlock(block, index=index)
        # TODO: find a more reliable way to do this (init indicator)
        self.refreshIndicator()
        log.info("added: {0}".format(self.builder.blocks))

    def addBlock(self, block):
        return self.blockListWidget.insertBlock(block)

    def deleteBlock(self, op):
        self.builder.blocks.remove(op)
        log.info("deleted: {0}".format(self.builder.blocks))

    def runItemCallback(self, item):
        index = self.blockListWidget.indexFromItem(item).row()
        self.setBuilderIndex(index)
        self.buildNext()



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
        icon = IconManager.get("start_from_here.png",type="icon")
        self.contextMenu.addCommand("start from here", self.setNextToSelected, icon=icon)


        self._currItemRow = None


    @property
    def builder(self):
        return self.blueprintWidget.builder

    @property
    def opWidgets(self):
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
            self.itemOrderChanged.emit()
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

    def dropEvent( self, event ):

        data = event.mimeData()

        source = event.source()
        if isinstance(source,BlockListWidget):
            # self.setDragDropMode(self.InternalMove)
            ret = super(BlockListWidget, self).dropEvent(event)
            # self.setDragDropMode(self.DragDrop)
            return ret

        elif isinstance(source, BlockMenuListWidget):
            # DIRTY TRICK TO GET WHERE THE NEW ITEM SHOULD BE INSERTED
            # use default behaviour of dropevent to put the item
            super(BlockListWidget, self).dropEvent(event)
            idx = 0
            insertIndex = -1
            while idx < range(self.count()):
                item = self.item(idx)
                if not hasattr(item,"widget"):
                    insertIndex = idx
                    self.takeItem(idx)
                    break

                idx+=1
            #########################################


            blockTypes = [each.path() for each in data.urls()]

            for blockType in blockTypes:

                currentIndex = self.currentIndex()

                blockCls = lib.getBlockClassByName(blockType)
                op = blockCls()

                nextUniqueName = self.blueprintWidget.getNextUniqueName()
                op.name = nextUniqueName



                self.blueprintWidget.insertBlock(op, index=insertIndex)



        # urls = data.urls()
        # if ( urls and urls[0].scheme() == 'file' ):
        #     # for some reason, this doubles up the intro slash
        #     filepath = str(urls[0].path())[1:]
        #     self.setText(filepath)
        #     self.editingFinished.emit()
        #

    def allItems(self):
        return [self.item(idx) for idx in range(self.count())]


    def addBlock(self, block):
        index = self.count()
        self.insertBlock(block,index)


    def insertBlock(self, block, index=-1):
        if index<0:
            index = self.count()

        item = BlockItem()
        if block.__class__.__name__ == 'BreakPoint':
            item.setSizeHint(QtCore.QSize(50, 40))
            opWidget = BreakpointWidget(block, item)
        else:
            item.setSizeHint(QtCore.QSize(50, 80))
            opWidget = BlockWidget(block, item)
            opWidget.runBlockSignal.connect(self.runBlockCallback)
        opWidget.itemDeleted.connect(self.deleteBlock)
        item.widget, opWidget.item = opWidget, item

        self.insertItem(index, item)
        self.builder.addBlock(block)
        self.setItemWidget(item, opWidget)
        self.setCurrentItem(item)

    def runBlockCallback(self, item):
        index = self.indexFromItem(item).row()
        self.blueprintWidget.setBuilderIndex(index)
        self.blueprintWidget.buildNext()

    def deleteBlock(self, op):
        self.builder.blocks.remove(op)
        log.info("deleted: {0}".format(self.builder.blocks))

class BlockItem(QtWidgets.QListWidgetItem):
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
        self.initAttrs(base.GenericBuilder)

from brick.ui.components import block_widget, breakpoint_widget
class BaseBlockWidget(QtWidgets.QWidget):
    itemDeleted = QtCore.Signal(object)

    def __init__(self, op, item, parent=None):
        super(BaseBlockWidget, self).__init__(parent=parent)
        self.op = op
        self.item = item
        self._headerStyleSheet = None

    # def createOp(self):
    #     data = OrderedDict()
    #     data['type'] = self.op.__class__.__name__
    #     data['name'] = ""
    #     data['notes'] = ""
    #     data['attrs'] = {}
    #     data['inputs'] = {}
    #     data['active'] = self.activeCheckBox.isChecked()

        # return self.op.load(data)

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

        self.setEnableDisplay(currState)


class BreakpointWidget(BaseBlockWidget, breakpoint_widget.BreakPointWidget):
    def __init__(self, op, item, parent=None):
        super(BreakpointWidget, self).__init__(op, item, parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.op = op
        self.initSignals()

    def switchIndicator(self, state):
        return

    def syncData(self):
        data = OrderedDict()
        data['type'] = self.op.__class__.__name__
        data['active'] = self.activeCheckBox.isChecked()
        return data


class BlockWidget(BaseBlockWidget, block_widget.BlockWidget):
    runBlockSignal = QtCore.Signal(BlockItem)
    def __init__(self, op, item, parent=None):
        super(BlockWidget, self).__init__(op, item, parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.editorWidget=None

        self.op = op

        self.blockType.setText(op.__class__.__name__)

        # self.attrTree = AttrTree(self)

        # self.attrTreeLayout.addWidget(self.attrTree)

        self.initSignals()
        self.loadData()

    def initSignals(self):
        super(BlockWidget, self).initSignals()
        self.blockName.textEdited.connect(self.editNameChange)
        self.runBlockButton.clicked.connect(self.runBlockCalled)

    def editNameChange(self):
        self.op.name = self.blockName.text()

    def loadData(self):
        op = self.op
        self.blockName.setText(op.name)


    def runBlockCalled(self):
        self.runBlockSignal.emit(self.item)


    def syncData(self):
        data = OrderedDict()
        data['type'] = self.op.__class__.__name__
        data['name'] = self.blockName.text()
        data['notes'] = ""


        editorData = self.editorWidget.getData()

        for dataName, dataValue in editorData.items():
            data[dataName] = dataValue


        data['active'] = self.activeCheckBox.isChecked()


        self.op.reload(data)

    # def createOp(self):
    #     data = self.genData()
    #     return self.op.load(data)

    def sizeUp(self):
        item = self.item
        numItem = self.attrTree.topLevelItemCount()
        baseHeight = 150
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
        # self._parent.sizeUp()

    def setAttr(self, key, val):
        for item in self.allItems():
            if key == item.attrName:
                item.setValue(val)


    def allItems(self):
        items  = []
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            items.append(item)

        return items

    def addInput(self, inputData):
        inputItem = AttrItem(inputData)
        self.addTopLevelItem(inputItem)
        inputItem.setWidget()
        # self._parent.sizeUp()

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

        self.fieldWidget.editFinished.connect(Main_UI.ui.editorWidget.syncData)

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
        self.addButton = buttonBox.addButton("Add", QtWidgets.QDialogButtonBox.AcceptRole)
        self.addButton.setEnabled(True)
        self.closeButton = buttonBox.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)

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
        self.addButton.released.connect(self._addAttr)
        self.closeButton.released.connect(self.close)

    def _addAttr(self):
        attrName = self.__attrNameInput.text()

        if not attrName:
            log.warn("please fill the attribute name.")
            return

        attrType = attrtype.Input
        defaultValue = None
        self.parentWidget().addAttr((attrName, (attrType, defaultValue)))
        self.close()



class Block_Editor_Widget(QtWidgets.QWidget):
    def __init__(self, blockWidget=None, **kwargs):
        super(Block_Editor_Widget, self).__init__(**kwargs)
        self.blockWidget = blockWidget
        layout = VBoxLayout(self)
        with layout:
            qcreate(Button, "1")

    @property
    def op(self):
        return self.blockWidget.op

    def syncData(self):
        if self.blockWidget:

            self.blockWidget.syncData()

    def clear(self):
        layout = self.layout()
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self.blockWidget = None

    def update(self, blockWidget):
        self.blockWidget = blockWidget
        self.blockWidget.editorWidget = self
        self.attrTree = AttrTree(self)
        self.layout().addWidget(self.attrTree)

        op = self.op


        # if not hasattr(op, 'attrs') or not getattr(op, 'attrs'):
        for fixedAttr in self.op.fixedAttrs:
            aname, (atype, aval) = fixedAttr
            self.attrTree.addAttr(fixedAttr)
            if aname in op.attrs:
                val = op.attrs.get(aname)
                self.attrTree.setAttr(aname, val)

        for key, val in op.attrs.items():
            if key not in self.attrTree.attrs():
                attrType = type(val)
                data = (key, (attrType, val))
                self.attrTree.addAttr(data)

        for key, val in op.inputs.iteritems():
            if key not in self.attrTree.attrs():
                data = (key, (type(val), val))
                self.attrTree.addAttr(data)

    def getData(self):
        data = {}
        data['attrs'] = OrderedDict()
        data['inputs'] = OrderedDict()
        if self.attrTree:
            for idx in range(self.attrTree.topLevelItemCount()):
                item = self.attrTree.topLevelItem(idx)

                name = item.getName()
                value = item.getValue()

                if item.attrType == attrtype.Input:

                    data['inputs'][name] = value

                else:
                    data['attrs'][name] = value
        return data

class Property_Widget(QtWidgets.QWidget):
    def __init__(self,*args,**kwargs):
        super(Property_Widget, self).__init__(*args,**kwargs)
        layout = VBoxLayout(self)
        with layout:
            qcreate(Button,"1")
            qcreate(Button,"2")




class Editor_Dock(QtWidgets.QDockWidget):
    def __init__(self,*args,**kwargs):
        super(Editor_Dock, self).__init__(*args,**kwargs)
        self.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mainWidget = Block_Editor_Widget()
        self.setWidget(self.mainWidget)
        self.setFloating(False)



def ui():
    ui = BrickUI.launch()
    return ui