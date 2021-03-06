import os
from qqt import QtWidgets, QtGui, QtCore
from Qt.QtCompat import loadUi
from brick.lib.path import Path
from brick.base import log, unicode

from brick.constants import BLUEPRINT_EXTENSION
from brick import lib

UIDIR = os.path.dirname(__file__)

import brick.settings as settings

from brick.ui import IconManager



class DeleteButton(QtWidgets.QPushButton):
    """
    A simple delete button to be attached to treeWidgetItem.
    """
    def __init__(self, *args, **kwargs):
        super(DeleteButton, self).__init__(*args, **kwargs)
        icon = IconManager.get('trashbin.svg',type="icon")
        self.setIcon(icon)
        self.setFlat(True)
        sizePol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setSizePolicy(sizePol)
        self.setMaximumWidth(14)
        self.setMaximumHeight(18)


class BlueprintTreeWidget(QtWidgets.QTreeWidget):
    """
    A treeWidget to list (and delete) existing blueprints.
    """
    headerLabels = ['Blueprint Name', 'Notes', 'Delete']

    def __init__(self, mainWidget, parent=None):
        super(BlueprintTreeWidget, self).__init__(parent=parent)
        self._mainWidget = mainWidget
        self._initUI()
        self._connectSignals()

    def _initUI(self):
        self.setColumnCount(len(self.headerLabels))
        self.setHeaderLabels(self.headerLabels)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 100)

    def _connectSignals(self):
        self.itemSelectionChanged.connect(self.updateRelatedFields)

    def updateRelatedFields(self):
        """
        update parent fields based on item selection.
        """
        try:
            currItem = self.selectedItems()[0]
        except IndexError:
            return

        self._mainWidget.blueprintNameField.setText(currItem.name)

        self._mainWidget.notesField.setPlainText(currItem.notes)

    def deleteItem(self, item):
        """
        delete blueprint file and remove item from list.
        """
        tempatePath = item.filePath
        if tempatePath.exists():
            tempatePath.remove()

        idx = self.indexOfTopLevelItem(item)
        self.takeTopLevelItem(idx)

    def addTopLevelItem(self, item):
        """
        set the delete button widget after adding item.
        need to do it here because we haven't specified parent treeWidget when creating treeWidgetItem,
        so it could not be done in creation time.
        """
        super(BlueprintTreeWidget, self).addTopLevelItem(item)
        self.setItemWidget(item, 3, item.deleteButton)


class BlueprintTreeItem(QtWidgets.QTreeWidgetItem):
    """
    item to display blueprint and its information.
    """
    def __init__(self, filePath, parent=None):
        super(BlueprintTreeItem, self).__init__(parent=parent)
        self._filePath = filePath
        self._name = None
        self._notes = None
        self.deleteButton = None
        self.loadData()


    @property
    def name(self):
        return self._name

    @property
    def notes(self):
        return self._notes

    @property
    def filePath(self):
        return self._filePath

    def loadData(self):
        blueprintData = lib.loadData(self._filePath) or {}

        self._name = self._filePath.baseName()
        self._notes = blueprintData.get('notes', None)

        if self.isValid():
            # column 0
            self.setText(0, self._name)

            # column 1
            self.setText(1, self._notes)

            # column 2
            self.deleteButton = DeleteButton()
            self.deleteButton.clicked.connect(self.removeItem)
            self.setSizeHint(2, QtCore.QSize(15, 15))

    def isValid(self):
        return all([self._name])

    def removeItem(self):
        reply = QtWidgets.QMessageBox.question(None,
                                           'Message',
                                           "Are you sure to delete this blueprint?",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                                           QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            treeWidget = self.treeWidget()
            treeWidget.deleteItem(self)


class BaseSaveLoadDialog(QtWidgets.QDialog):
    """
    A base class for save /import blueprint dialog.
    """
    _uifile = os.path.join(UIDIR, "saveLoadBlueprintDialog.ui")

    setting_file_updated_signal = QtCore.Signal()

    def __init__(self, parentDialog=None):
        super(BaseSaveLoadDialog, self).__init__()
        loadUi(self._uifile, self)
        self.parentDialog = parentDialog
        self.initUI()
        self.initSignals()
        self.initData()

    def initUI(self):
        icon = IconManager.get("load.png",type="icon")
        self.browseFolderButton.setIcon(icon)

        self.blueprintTreeWidget = BlueprintTreeWidget(self)

        self.blueprintListLayout.addWidget(self.blueprintTreeWidget)

    def initSignals(self):
        self.baseDirField.textChanged.connect(self.populateBlueprintList)
        self.browseFolderButton.clicked.connect(self.browseFolder)

    def browseFolder(self):
        baseDir = settings.getLastOpenedDir()
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Set Dir',
                                                        baseDir)
        if dirPath:
            settings.setLastOpenedDir(dirPath)
            self.baseDirField.setText(dirPath)
            self.populateBlueprintList()

    def populateBlueprintList(self):
        self.blueprintTreeWidget.clear()

        baseDir = Path(self.baseDirField.text())

        if not baseDir.exists():
            return

        for eachFile in baseDir.listdir():
            if not eachFile.endswith(BLUEPRINT_EXTENSION):
                continue

            try:
                newItem = BlueprintTreeItem(eachFile)
            except ValueError:
                continue
            if newItem.isValid():
                self.blueprintTreeWidget.addTopLevelItem(newItem)
                self.blueprintTreeWidget.setItemWidget(newItem, 2, newItem.deleteButton)


    def initData(self):
        baseDir = settings.getLastOpenedDir()
        self.baseDirField.setText(baseDir)
        self.populateBlueprintList()


class LoadBlueprintDialog(BaseSaveLoadDialog):
    load_signal = QtCore.Signal(unicode)
    def initUI(self):
        super(LoadBlueprintDialog, self).initUI()
        self.blueprintNameLabel.setParent(None)
        self.blueprintNameField.setParent(None)
        self.notesField.setParent(None)
        self.notesLabel.setParent(None)

        self.loadButton = QtWidgets.QPushButton('Load')
        self.actionButtonLayout.addWidget(self.loadButton)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.actionButtonLayout.addWidget(self.cancelButton)


    def initSignals(self):
        super(LoadBlueprintDialog, self).initSignals()
        self.loadButton.clicked.connect(self.callLoadBlueprint)
        self.cancelButton.clicked.connect(self.close)
        self.blueprintTreeWidget.itemDoubleClicked.connect(self.callLoadBlueprint)

    def callLoadBlueprint(self):
        baseDir = Path(self.baseDirField.text())

        selectedBlueprint = self.blueprintTreeWidget.currentItem()
        fileName = selectedBlueprint.name

        filePath = baseDir / fileName


        settings.addRecentBlueprint(filePath)

        self.setting_file_updated_signal.emit()

        self.load_signal.emit(filePath)


        self.close()


class SaveBlueprintDialog(BaseSaveLoadDialog):
    saveSignalled = QtCore.Signal(tuple)

    def __init__(self, parentDialog):
        super(SaveBlueprintDialog, self).__init__(parentDialog=parentDialog)

    def initUI(self):
        super(SaveBlueprintDialog, self).initUI()
        self.saveButton = QtWidgets.QPushButton('Save')
        self.actionButtonLayout.addWidget(self.saveButton)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.actionButtonLayout.addWidget(self.cancelButton)


    def initSignals(self):
        super(SaveBlueprintDialog, self).initSignals()
        self.saveButton.clicked.connect(self.callSaveBlueprint)
        self.cancelButton.clicked.connect(self.close)
        self.blueprintTreeWidget.itemDoubleClicked.connect(self.callSaveBlueprint)
        self.blueprintNameField.returnPressed.connect(self.callSaveBlueprint)

    def callSaveBlueprint(self):
        baseDir = Path(self.baseDirField.text())
        blueprintName = Path(self.blueprintNameField.text())
        notes = self.notesField.toPlainText() or ""

        if not all([baseDir, blueprintName]):
            log.warn("please fill all input fields.")
            return

        if not blueprintName.endswith(BLUEPRINT_EXTENSION):
            blueprintName = blueprintName + BLUEPRINT_EXTENSION

        blueprintPath = baseDir / blueprintName

        if blueprintPath.exists():
            confirm = QtWidgets.QMessageBox.question(None,
                                                 'Message',
                                                 "file exists. overwrite?",
                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                 QtWidgets.QMessageBox.No)
            if confirm == QtWidgets.QMessageBox.No:
                return

        if not baseDir.exists():
            baseDir.makeDirs()

        log.info('saved blueprint path: {0}'.format(blueprintPath))
        settings.addRecentBlueprint(blueprintPath)
        self.setting_file_updated_signal.emit()
        self.saveSignalled.emit((blueprintPath, notes))
        # self.parentDialog.blueprintWidget.save(blueprintPath, notes)


        self.close()
