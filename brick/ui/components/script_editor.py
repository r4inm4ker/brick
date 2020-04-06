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


class PythonTextEditor(QtWidgets.QTextEdit):
    def __init__(self,*args,**kwargs):
        super(PythonTextEditor, self).__init__(*args,**kwargs)

        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        font.setPointSize(11)
        self.setFont(font)

        tabStop = 4
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopWidth(tabStop * metrics.width(' '))

        highlight = PythonHighlighter(self.document())

        self.textChanged.connect(self.convertTabToSpace)

    def convertTabToSpace(self):
        pass
        # disable this first until we can make it reliable
        '''
        cur = self.textCursor()
        if cur.previousChar == '\t':
            print "CONVERT TAB TO SPACE"
            cur.deletePreviousChar()
            cur.insertText('    ')

            # self.text_edit.insertPlainText('    ')
        '''

    def getCurrentText(self):
        currentScript = self.toPlainText()

        lines = currentScript.split("\n")

        savedLines = []
        for line in lines:
            preprend = ""
            while line.startswith("\t"):
                preprend = preprend + "    "
                line = line.replace("\t","",1)

            savedLines.append(preprend+line)

        convertedScript = "\n".join(savedLines)
        # convertedScript = currentScript.replace('\t', '    ')
        return convertedScript

#
# # !/usr/bin/env python
# # -*- coding: utf-8 -*-
#
# import sys
# from qqt import QtWidgets, QtCore
# import qdarkstyle
#
# if __name__ == '__main__':
#     app = QtWidgets.QApplication([])
#
#     # app.setStyleSheet(qdarkstyle.load_stylesheet_pyside())
#
#     ui = ScriptEditor()
#     ui.show()
#
#     sys.exit(app.exec_())
