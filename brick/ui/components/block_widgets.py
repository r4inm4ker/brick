from collections import OrderedDict
from qqt import QtCore, QtGui, QtWidgets
from qqt.gui import qcreate, HBoxLayout, VBoxLayout, Button, StringField, Spacer, Checkbox, SeparatorLine

class BaseBlockWidget(QtWidgets.QWidget):
    itemDeleted = QtCore.Signal(object)
    activeStateEdited = QtCore.Signal(bool)
    nameEdited = QtCore.Signal(str)
    runBlockSignal = QtCore.Signal(object)

    def __init__(self, block, item, parent=None):
        super(BaseBlockWidget, self).__init__(parent=parent)
        self.editorWidget = None
        self.deleteButton = None
        self.activeCheckBox = None
        self.blockNameField = None
        self.block = block
        self.item = item
        self._headerStyleSheet = None

    def initSignals(self):
        self.deleteButton.clicked.connect(self.delete)
        self.activeCheckBox.clicked.connect(self.switchActiveState)
        self.blockNameField.editingFinished.connect(self.blockNameFieldEdited)

    def delete(self):
        self.itemDeleted.emit(self.block)
        item = self.item
        lw = item.listWidget()
        idx = lw.indexFromItem(item).row()
        lw.takeItem(idx)

    def switchActiveState(self):
        currState = self.activeCheckBox.isChecked()
        self.setEnableDisplay(currState)
        self.activeStateEdited.emit(currState)

    def blockNameFieldEdited(self):
        val = self.blockNameField.getValue()
        self.nameEdited.emit(str)

    def switchIndicator(self, state):
        return


class BlockWidget(BaseBlockWidget):

    def __init__(self, *args, **kwargs):
        super(BlockWidget, self).__init__(*args,**kwargs)

        layout = VBoxLayout(self)
        layout.setContentsMargins(2,0,2,0)
        with layout:
            mainLayout = qcreate(HBoxLayout)
            mainLayout.setContentsMargins(0,0,0,0)
            with mainLayout:
                self.indicatorWidget = qcreate(QtWidgets.QStackedWidget)
                self.indicatorWidget.setFixedWidth(15)
                self.nothing = qcreate(QtWidgets.QLabel)
                self.nothing.setStyleSheet('background-color:rgb(126, 126, 126)')
                self.success = qcreate(QtWidgets.QLabel)
                self.success.setStyleSheet('background-color:rgb(52, 141, 3)')
                self.fail = qcreate(QtWidgets.QLabel)
                self.fail.setStyleSheet('background-color:rgb(149, 0, 2)')
                self.next = qcreate(QtWidgets.QLabel)
                self.next.setStyleSheet('background-color:rgb(244, 244, 0)')

                self.indicatorWidget.addWidget(self.nothing)
                self.indicatorWidget.addWidget(self.success)
                self.indicatorWidget.addWidget(self.fail)
                self.indicatorWidget.addWidget(self.next)

                # self.indicatorWidget.setCurrentIndex(1)

                self.frame = qcreate(QtWidgets.QFrame,layoutType=HBoxLayout)
                self.frame.layout().setContentsMargins(0, 0, 0, 0)
                with self.frame.layout():

                    self.activeCheckBox = qcreate(Checkbox)
                    self.blockTypeLabel = qcreate(QtWidgets.QLabel,"Block Type")
                    self.blockNameField = qcreate(StringField)
                    # qcreate(Spacer)
                    # self.annotationBtn = qcreate(Button,"?")

                    self.runBlockButton = qcreate(Button, ">")

                    qcreate(Spacer)


                with qcreate(VBoxLayout):
                    self.deleteButton = qcreate(Button, "x")


                    # self.runBlockButton = qcreate(Button,">")
                    # self.runBlockButton.setFixedWidth(20)
                    # self.runBlockButton.setFixedHeight(60)

            qcreate(SeparatorLine)

        self.setEnableDisplay(True)


        self.blockTypeLabel.setText(self.block.__class__.__name__)
        self.blockNameField.setValue(self.block.name)

    def initSignals(self):
        super(BlockWidget, self).initSignals()
        self.runBlockButton.clicked.connect(self.runBlockCalled)

    def setEnableDisplay(self, enabled):
        if enabled:
            self.setStyleSheet('')
        else:
            self.setStyleSheet("""QWidget {background-color:gray;}""")

    def editNameChange(self):
        self.block.name = self.blockNameField.text()

    def loadData(self):
        block = self.block
        self.blockName.setText(block.name)

    def runBlockCalled(self):
        self.runBlockSignal.emit(self.item)

    def syncData(self):
        data = OrderedDict()
        data['type'] = self.block.__class__.__name__
        data['name'] = self.blockName.text()
        data['notes'] = ""

        editorData = self.editorWidget.getData()

        for dataName, dataValue in editorData.items():
            data[dataName] = dataValue

        data['active'] = self.activeCheckBox.isChecked()

        self.block.reload(data)

    def switchIndicator(self, state):
        self.indicatorWidget.setCurrentIndex(state)




class BreakPointWidget(BaseBlockWidget):
    def __init__(self, *args, **kwargs):
        super(BreakPointWidget, self).__init__(*args,**kwargs)

        layout = VBoxLayout(self)
        layout.setContentsMargins(2,0,2,0)
        with layout:
            mainLayout = qcreate(HBoxLayout)
            mainLayout.setContentsMargins(0,0,0,0)
            with mainLayout:
                self.indicatorWidget = qcreate(QtWidgets.QStackedWidget)
                self.indicatorWidget.setFixedWidth(15)
                self.nothing = qcreate(QtWidgets.QLabel)
                self.indicatorWidget.addWidget(self.nothing)

                self.frame = qcreate(QtWidgets.QFrame,layoutType=HBoxLayout)
                self.frame.layout().setContentsMargins(0, 0, 0, 0)
                with self.frame.layout():
                    self.activeCheckBox = qcreate(Checkbox)
                    self.blockType = qcreate(QtWidgets.QLabel,"Break Point")
                    qcreate(Spacer)

                with qcreate(VBoxLayout):
                    self.deleteButton = qcreate(Button, "x")


            qcreate(SeparatorLine)


        self.setEnableDisplay(True)


    def setEnableDisplay(self, enabled):
        if enabled:
            self.setStyleSheet('background-color:rgb(127, 35, 35)')
        else:
            self.setStyleSheet("""QWidget {background-color:gray;}""")


    def syncData(self):
        data = OrderedDict()
        data['type'] = self.block.__class__.__name__
        data['active'] = self.activeCheckBox.isChecked()
        return data
