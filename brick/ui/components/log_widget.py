import sys
from qqt import QtWidgets, QtCore, QtGui

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.Signal(str)

    def write(self, text):
        self.textWritten.emit(text)

class Log_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Log_Widget, self).__init__(parent=parent)

        # Install the custom output stream
        sys.stdout = EmittingStream()
        sys.stdout.textWritten.connect(self.normalOutputWritten)

        # self.rout = sys.stdout

        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setMinimumHeight(120)
        layout.addWidget(self.textEdit)


    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        # Maybe QTextEdit.append() works as well, but this is how I do it:
        cursor = self.textEdit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textEdit.setTextCursor(cursor)
        self.textEdit.ensureCursorVisible()