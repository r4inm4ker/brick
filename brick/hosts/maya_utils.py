import maya.cmds as mc
from qqt import QtGui, QtCore, QtWidgets
from qqt.gui import VBoxLayout
from qqt.lib import wrapInstance

import maya.OpenMayaUI as omui


def convertMayaControl(ctlName):
    ptr = omui.MQtUtil.findControl(ctlName)
    attrWidget = wrapInstance(int(ptr), QtWidgets.QWidget)
    return attrWidget

class Maya_Log_Widget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(Maya_Log_Widget, self).__init__(*args, **kwargs)
        self._initUI()

    def _initUI(self):
        layout = VBoxLayout(self)
        mc.window()
        mc.columnLayout()
        outputLog = mc.cmdScrollFieldReporter(clr=True)
        self.output_log_widget = convertMayaControl(outputLog)
        layout.addWidget(self.output_log_widget)

