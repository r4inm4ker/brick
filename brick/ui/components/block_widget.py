from qqt import QtCore, QtGui, QtWidgets
from qqt.gui import qcreate, HBoxLayout, VBoxLayout, Button, StringField, Spacer, Checkbox, SeparatorLine

class BlockWidget(QtWidgets.QWidget):
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

                self.frame = qcreate(QtWidgets.QFrame,layoutType=VBoxLayout)
                with self.frame.layout():
                    self.headerWidget = qcreate(QtWidgets.QWidget,layoutType=HBoxLayout)
                    with self.headerWidget.layout():
                        self.activeCheckBox = qcreate(Checkbox)
                        self.blockType = qcreate(QtWidgets.QLabel,"Block Type")
                        self.blockName = qcreate(StringField)
                        qcreate(Spacer)
                        # self.annotationBtn = qcreate(Button,"?")



                    self.attrTreeLayout = qcreate(VBoxLayout)

                with qcreate(VBoxLayout):
                    self.deleteButton = qcreate(Button, "x")


                    self.runBlockButton = qcreate(Button,">")
                    self.runBlockButton.setFixedWidth(20)
                    self.runBlockButton.setFixedHeight(60)

            qcreate(SeparatorLine)

