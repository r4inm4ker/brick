from qqt import QtGui, QtCore, QtWidgets
from qqt.gui import qcreate, VBoxLayout, HBoxLayout, Button
from brick.ui.lib.python_syntax import PythonHighlighter
from brick.ui import IconManager
from brick import attr_type


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
            self.editor = qcreate(PythonTextEditor)



            with qcreate(HBoxLayout) as hlayout:
                icon = IconManager.get("save.png",type='icon')
                self.setBtn = qcreate(Button, 'Save', icon=icon)
                self.cancelBtn = qcreate(Button, 'Cancel')

            hlayout.setRatio(2, 1)

        layout.setRatio(1, 0)

        self.resize(800,800)


    def initSignal(self):
        self.cancelBtn.clicked.connect(self.close)
        self.setBtn.clicked.connect(self.setScript)

    def loadScript(self, script):
        self.editor.setPlainText(script)

    def setScript(self):
        currentScript = self.editor.getCurrentText()

        self._parent.scriptField.setText(currentScript)
        self._parent.emitSignal()

        self.close()


class PythonTextEditor(QtWidgets.QPlainTextEdit):
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
        convertedScript = attr_type.Script(currentScript.replace('\n', r'\n'))
        convertedScript = convertedScript.replace('\t', '    ')
        return convertedScript

    # there's still some glitch with tabbing after save(converted to space).
    # disable for now
    # def keyPressEvent(self, event):
    #     tab_char = '\t'  # could be anything including spaces
    #     if event.key() == QtCore.Qt.Key_Backtab:
    #         # get current cursor
    #         cur = self.textCursor()
    #         cur.clearSelection()
    #
    #         # move to begining of line and select text to first word
    #         cur.movePosition(QtGui.QTextCursor.StartOfLine)
    #         cur.movePosition(QtGui.QTextCursor.NextWord, QtGui.QTextCursor.KeepAnchor)
    #         sel_text = cur.selectedText()
    #
    #         # if the text starts with the tab_char, replace it
    #         if sel_text.startswith(tab_char):
    #             text = sel_text.replace(tab_char, '', 1)
    #             cur.insertText(text)
    #         elif sel_text.startswith(' '):
    #             text = sel_text.replace(' ', '', 4)
    #             cur.insertText(text)
    #
    #     else:
    #         return QtWidgets.QPlainTextEdit.keyPressEvent(self, event)