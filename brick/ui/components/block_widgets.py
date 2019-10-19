from collections import OrderedDict
from qqt import QtCore, QtGui, QtWidgets
from qqt.gui import qcreate, HBoxLayout, VBoxLayout, Button, StringField, Spacer, Checkbox, SeparatorLine
from brick.ui import IconManager

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



    def _connectSignals(self):
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

        self.syncData()
        self.activeStateEdited.emit(currState)

    def blockNameFieldEdited(self):
        val = self.blockNameField.getValue()
        self.syncData()
        self.nameEdited.emit(val)

    def switchIndicator(self, state):
        return

    def syncData(self):
        return

    def currentName(self):
        return self.blockNameField.getValue()

class BlockWidget(BaseBlockWidget):

    def __init__(self, *args, **kwargs):
        super(BlockWidget, self).__init__(*args,**kwargs)
        self._initUI()
        self._connectSignals()

    def _initUI(self):
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
                    # icon = IconManager.get("play.svg", type="icon")
                    # self.runBlockButton = qcreate(Button, icon, "")

                    qcreate(Spacer)


                with qcreate(VBoxLayout):
                    with qcreate(HBoxLayout):
                        icon = IconManager.get("play.svg", type="icon")
                        self.runBlockButton = qcreate(Button, icon, "")

                        qcreate(QtWidgets.QLabel,"  ")

                        icon = IconManager.get("delete.svg", type="icon")
                        self.deleteButton = qcreate(Button, "",icon=icon)
                        self.deleteButton.setFixedSize(QtCore.QSize(15,15))


                    # self.runBlockButton = qcreate(Button,">")
                    # self.runBlockButton.setFixedWidth(20)
                    # self.runBlockButton.setFixedHeight(60)

            qcreate(SeparatorLine)

        # self.setEnableDisplay(True)


        self.blockTypeLabel.setText("{} : ".format(self.block.__class__.__name__))
        self.blockNameField.setValue(self.block.name)
        self.activeCheckBox.setValue(self.block.active)
        self.setEnableDisplay(self.block.active)


    def _connectSignals(self):
        super(BlockWidget, self)._connectSignals()
        self.runBlockButton.clicked.connect(self.runBlockCalled)

    def setEnableDisplay(self, enabled):
        if enabled:
            self.setStyleSheet('')
        else:
            self.setStyleSheet("""QWidget {background-color:gray;}""")


    def runBlockCalled(self):
        self.runBlockSignal.emit(self)

    def syncData(self):
        data = OrderedDict()
        data['name'] = self.blockNameField.text()
        data['active'] = self.activeCheckBox.isChecked()

        self.block.reload(data)

    def switchIndicator(self, state):
        self.indicatorWidget.setCurrentIndex(state)




class BreakPointWidget(BaseBlockWidget):
    def __init__(self, *args, **kwargs):
        super(BreakPointWidget, self).__init__(*args,**kwargs)
        self._initUI()
        self._connectSignals()

    def _initUI(self):
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
                    self.blockNameField = qcreate(StringField)
                    self.blockNameField.setHidden(True)
                    qcreate(Spacer)

                with qcreate(VBoxLayout):
                    icon = IconManager.get("delete.svg", type="icon")
                    self.deleteButton = qcreate(Button, "", icon=icon)
                    self.deleteButton.setFixedSize(QtCore.QSize(15, 15))


            qcreate(SeparatorLine)


        # self.setEnableDisplay(True)

        self.activeCheckBox.setValue(self.block.active)
        self.setEnableDisplay(self.block.active)


    def setEnableDisplay(self, enabled):
        if enabled:
            self.setStyleSheet('background-color:rgb(127, 35, 35)')
        else:
            self.setStyleSheet("""QWidget {background-color:gray;}""")


    def syncData(self):
        data = OrderedDict()
        data['active'] = self.activeCheckBox.isChecked()
        self.block.reload(data)
