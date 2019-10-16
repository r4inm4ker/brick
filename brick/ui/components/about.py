from qqt import QtWidgets, QtCore , QtGui
from qqt.gui import qcreate, HBoxLayout, VBoxLayout, Button


class About_Dialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(About_Dialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("About Brick")

        layout = VBoxLayout(self)
        with layout:
            textEdit = qcreate(QtWidgets.QTextEdit)

            textEdit.setPlainText('''
https://github.com/r4inm4ker/brick

by Jefri Haryono, released under MIT License

icons provided by https://icons8.com
            ''')

            textEdit.setReadOnly(True)

            # label = qcreate(QtWidgets.QLabel, "https://github.com/r4inm4ker/brick")
            # label.setAlignment(QtCore.Qt.AlignCenter)
            #
            # label = qcreate(QtWidgets.QLabel, "by Jefri Haryono, released under MIT License")
            # label.setAlignment(QtCore.Qt.AlignCenter)
            #
            # label = qcreate(QtWidgets.QLabel,"")
            #
            # label = qcreate(QtWidgets.QLabel, "icons provided by https://icons8.com")
            # label.setAlignment(QtCore.Qt.AlignCenter)

            label = qcreate(QtWidgets.QLabel, "")

            btn = qcreate(Button, "Ok")
            btn.clicked.connect(self.close)
