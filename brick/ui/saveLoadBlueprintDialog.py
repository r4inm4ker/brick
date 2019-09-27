import os
from Qt import QtWidgets, QtGui, QtCore
from Qt.QtCompat import loadUi
from brick.lib.path import Path

import logging

log = logging.getLogger("brick")

from brick.constants import BLUEPRINT_EXTENSION
from brick import lib

UIDIR = os.path.dirname(__file__)


class DeleteButton(QtWidgets.QPushButton):
    """
    A simple delete button to be attached to treeWidgetItem.
    """
    def __init__(self, *args, **kwargs):
        super(DeleteButton, self).__init__(*args, **kwargs)
        self.setText('x')
        self.setFlat(True)
        sizePol = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setSizePolicy(sizePol)
        self.setMaximumWidth(14)
        self.setMaximumHeight(18)


class BlueprintTreeWidget(QtWidgets.QTreeWidget):
    """
    A treeWidget to list (and delete) existing blueprints.
    """
    headerLabels = ['Blueprint Name', 'Variant', 'Notes', 'Delete']

    def __init__(self, mainWidget, parent=None):
        super(BlueprintTreeWidget, self).__init__(parent=parent)
        self._mainWidget = mainWidget
        self.initUI()
        self.initSignals()

    def initUI(self):
        self.setColumnCount(len(self.headerLabels))
        self.setHeaderLabels(self.headerLabels)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 100)

    def initSignals(self):
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
            self.deleteButton.released.connect(self.removeItem)

    def isValid(self):
        return all([self._name, self._notes])

    def removeItem(self):
        reply = QtWidgets.QMessageBox.question(None,
                                           'Message',
                                           "Are you sure to delete this resource(s)",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            treeWidget = self.treeWidget()
            treeWidget.deleteItem(self)


class AbstractBlueprintDialog(QtWidgets.QDialog):
    """
    A base class for save /import blueprint dialog.
    """
    _uifile = os.path.join(UIDIR, "saveLoadBlueprintDialog.ui")

    def __init__(self, parentDialog=None):
        super(AbstractBlueprintDialog, self).__init__()
        loadUi(self._uifile, self)
        self.parentDialog = parentDialog
        self.initUI()
        self.initSignals()
        self.initData()

    def initUI(self):
        self.blueprintTreeWidget = BlueprintTreeWidget(self)

        self.blueprintListLayout.addWidget(self.blueprintTreeWidget)

    def initSignals(self):
        self.baseDirField.textChanged.connect(self.populateBlueprintList)

    def populateBlueprintList(self):
        self.blueprintTreeWidget.clear()

        baseDir = Path(self.baseDirField.text())

        if not baseDir.exists():
            return

        for eachFile in baseDir.walkFiles():
            if not eachFile.endswith(BLUEPRINT_EXTENSION):
                continue

            newItem = BlueprintTreeItem(eachFile)

            if newItem.isValid():
                self.blueprintTreeWidget.addTopLevelItem(newItem)

    def updateBlueprintDir(self):
        baseDir = lib.getBlueprintDir()
        self.baseDirField.setText(baseDir)

    def initData(self):
        self.updateBlueprintDir()
        self.populateBlueprintList()


class LoadBlueprintDialog(AbstractBlueprintDialog):
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

    def callLoadBlueprint(self):
        baseDir = Path(self.baseDirField.text())

        selectedBlueprint = self.blueprintTreeWidget.currentItem()
        fileName = selectedBlueprint.name

        filePath = baseDir / fileName

        self.parentDialog.blueprintWidget.load(filePath)

        self.close()


class SaveBlueprintDialog(AbstractBlueprintDialog):
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

    def callSaveBlueprint(self):
        baseDir = Path(self.baseDirField.text())
        blueprintName = Path(self.blueprintNameField.text())
        notes = self.notesField.toPlainText()

        if not all([baseDir, blueprintName, notes]):
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

        self.parentDialog.blueprintWidget.save(blueprintPath, notes)

        confirmBox = QtWidgets.QMessageBox()
        confirmBox.setWindowTitle('Blueprint Saved')
        confirmBox.setText("blueprint {0} saved".format(blueprintName))
        confirmBox.exec_()

        self.close()
