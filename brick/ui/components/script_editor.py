from qqt import QtGui, QtCore, QtWidgets
from qqt.gui import qcreate, VBoxLayout, HBoxLayout, Button
from brick.ui.lib.python_syntax import PythonHighlighter
from brick.ui import IconManager
from brick import attr_type
from brick.base import unicode


class ScriptEditor(QtWidgets.QDialog):
    scriptAccepted = QtCore.Signal(unicode)

    def __init__(self, script=None):
        super(ScriptEditor, self).__init__()
        self.initUI()
        self.initSignal()
        if script:
            self.loadScript(script)

    def initUI(self):
        self.setWindowTitle('Script Editor')
        layout = VBoxLayout(self)
        with layout:
            self.editor = qcreate(PythonTextEditor)

            with qcreate(HBoxLayout) as hlayout:
                icon = IconManager.get("save.png", type='icon')
                self.setBtn = qcreate(Button, 'Save', icon=icon)
                self.cancelBtn = qcreate(Button, 'Cancel')

            hlayout.setRatio(2, 1)

        layout.setRatio(1, 0)

        self.resize(800, 800)

    def initSignal(self):
        self.cancelBtn.clicked.connect(self.close)
        self.setBtn.clicked.connect(self.acceptEdit)

    def loadScript(self, script):
        self.editor.setPlainText(script)

    def acceptEdit(self):
        currentScript = self.editor.getCurrentText()
        self.scriptAccepted.emit(currentScript)
        self.close()




from pyqode.core import modes, panels
from pyqode.python import modes as pymodes, widgets


class PythonTextEditor(widgets.PyCodeEditBase):
    def __init__(self, *args, **kwargs):
        super(PythonTextEditor, self).__init__(*args, **kwargs)

        #--- core panels
        self.panels.append(panels.LineNumberPanel())

        #--- core modes
        self.modes.append(modes.CaretLineHighlighterMode())
        self.modes.append(modes.ExtendedSelectionMode())
        self.modes.append(modes.SmartBackSpaceMode())
        self.modes.append(modes.SymbolMatcherMode())
        self.modes.append(modes.ZoomMode())

        #---  python specific modes
        self.modes.append(pymodes.CommentsMode())
        self.modes.append(pymodes.PyAutoIndentMode())
        self.modes.append(pymodes.PyIndenterMode())

        self.background = QtGui.QColor(0,0,0)
        self.foreground = QtGui.QColor(255,255,255)
        # self.setStyleSheet('')

        highlight = PythonHighlighter(self.document())



    def getCurrentText(self):
        currentScript = self.toPlainText()
        convertedScript = attr_type.Script(currentScript.replace('\n', r'\n'))
        convertedScript = convertedScript.replace('\t', '    ')
        return convertedScript


# !/usr/bin/env python
# -*- coding: utf-8 -*-


if __name__ == '__main__':
    import sys
    from qqt import QtWidgets, QtCore
    import qdarkstyle

    app = QtWidgets.QApplication([])

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyside())

    ui = ScriptEditor()
    ui.show()

    sys.exit(app.exec_())

