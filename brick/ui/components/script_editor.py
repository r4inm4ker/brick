from qqt import QtGui, QtCore, QtWidgets
from qqt.gui import qcreate, VBoxLayout, HBoxLayout, Button
from brick.ui.lib import PythonHighlighter
from brick.ui import IconManager
from brick import attrtype


class ScriptEditor(QtWidgets.QDialog):
    def __init__(self, currentScript, parent):
        super(ScriptEditor, self).__init__()
        self._parent = parent
        self.initUI()
        self.initSignal()
        self.loadScript(currentScript)

    def initUI(self):
        self.setWindowTitle('script editor')
        layout = VBoxLayout(self)
        with layout:
            self.editor = qcreate(QtWidgets.QPlainTextEdit)
            highlight = PythonHighlighter(self.editor.document())

            with qcreate(HBoxLayout) as hlayout:
                icon = IconManager.get("save.png",type='icon')
                self.setBtn = qcreate(Button, 'Save', icon=icon)
                self.cancelBtn = qcreate(Button, 'Cancel')

            hlayout.setRatio(2, 1)

        layout.setRatio(1, 0)

        self.resize(400,400)


    def initSignal(self):
        self.cancelBtn.clicked.connect(self.close)
        self.setBtn.clicked.connect(self.setScript)

    def loadScript(self, script):
        self.editor.setPlainText(script)

    def setScript(self):
        currentScript = self.editor.toPlainText()

        convertedScript = attrtype.Script(currentScript.replace('\n', r'\n'))

        self._parent.scriptField.setText(convertedScript)
        self._parent.emitSignal()

        self.close()