from Qt import QtCore, QtWidgets, QtGui
from brick import attrtype

class AttrField(object):
    editFinished = QtCore.Signal()

    @property
    def sizePolicy(self):
        return QtCore.QSizePolicy(QtCore.QSizePolicy.Preferred, QtCore.QSizePolicy.Fixed)

    def emitSignal(self):
        self.editFinished.emit()


class StringField(AttrField, QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(StringField, self).__init__(parent)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        self.setText(str(value))

    def getValue(self):
        return self.text()


class ScriptField(AttrField, QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ScriptField, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.scriptField = QtWidgets.QLineEdit()
        self.scriptField.setEnabled(False)
        layout.addWidget(self.scriptField)
        self.editButton = QtWidgets.QPushButton("edit")
        layout.addWidget(self.editButton)

        self.editButton.clicked.connect(self.openScriptEditor)

    def setValue(self, value):
        setVal = attrtype.Script(value.replace('\n', r'\n'))
        self.scriptField.setText(setVal)


    def openScriptEditor(self):
        currentScript = self.scriptField.text()
        convertedScript = attrtype.Script(currentScript.replace(r'\n', '\n'))
        editor = ScriptEditor(convertedScript, self)
        editor.exec_()

    def getValue(self):
        val = self.scriptField.text()
        return attrtype.Script(val.replace(r'\n', '\n'))


class ScriptEditor(QtWidgets.QDialog):
    def __init__(self, currentScript, parent):
        super(ScriptEditor, self).__init__()
        self._parent = parent
        self.initUI()
        self.initSignal()
        self.loadScript(currentScript)

    def initUI(self):
        self.setWindowTitle('script editor')
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.editor = QtWidgets.QPlainTextEdit()
        layout.addWidget(self.editor)
        layout.setStretch(layout.count() - 1, 1)

        hori = QtWidgets.QHBoxLayout()
        layout.addLayout(hori)
        layout.setStretch(layout.count() - 1, 0)

        self.cancelBtn = QtWidgets.QPushButton('cancel')
        hori.addWidget(self.cancelBtn)
        self.setBtn = QtWidgets.QPushButton('set')
        hori.addWidget(self.setBtn)

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


class IntField(AttrField, QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(IntField, self).__init__(parent)
        self.setMaximumWidth(90)
        self._validator = QtGui.QIntValidator()
        self.setValidator(self._validator)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        try:
            int(value)
        except (ValueError, TypeError):
            value = 0
        finally:
            self.setText(str(value))

    def getValue(self):
        text = self.text()
        retVal = 0
        try:
            retVal = int(text)
        except ValueError:
            pass
        return retVal

class BoolField(AttrField, QtWidgets.QLineEdit):
    True_ = str(True)
    False_ = str(False)

    def __init__(self, parent=None):
        super(BoolField, self).__init__(parent)
        self.setMaximumWidth(90)
        self.textEdited.connect(self.emitFieldChanged)
        self.editingFinished.connect(self.convertValue)

    def setValue(self, value):
        try:
            bool(value)
        except (ValueError, TypeError):
            value = False
        finally:
            self.setText(str(value))

    def getValue(self):
        text = self.text()
        try:
            if text == self.True_:
                return True
            elif text == self.False_:
                return False
        except ValueError:
            return False

    def convertValue(self):
        text = self.text()
        try:
            if text.lower() == self.True_.lower():
                self.setText(self.True_)
            elif text.lower() == self.False_.lower():
                self.setText(self.False_)
            elif int(text) > 0:
                self.setText(self.True_)
            else:
                self.setText(self.False_)
        except ValueError:
            self.setText(self.False_)
        self.emitSignal()

class FloatField(AttrField, QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(FloatField, self).__init__(parent)
        self.setMaximumWidth(90)
        self._validator = QtGui.QDoubleValidator()
        self.setValidator(self._validator)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        try:
            float(value)
        except (ValueError, TypeError):
            value = 0
        finally:
            self.setText(str(value))

    def getValue(self):
        text = self.text()
        retVal = 0.0
        try:
            retVal = float(text)
        except ValueError:
            pass
        return retVal

class ChooserField(AttrField, QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(ChooserField, self).__init__(parent)
        self._setupUI()
        self._setupSignal()

    def _setupUI(self):
        self.reloadItems()

    def _setupSignal(self):
        self.activated.connect(self.emitSignal)

    def reloadItems(self):
        while self.count() > 0:
            for idx in range(self.count()):
                self.removeItem(idx)

        for itemStr, itemData in self.items:
            self.addItem(itemStr, userData=itemData)

    @property
    def items(self):
        """
        must be implemented.
        """
        return []

    def getValue(self):
        return self.currentText()

    def getData(self):
        idx = self.currentIndex()
        return self.itemData(idx)

    def setValue(self, value):
        idx = self.findText(value)
        if idx >= 0:
            self.setCurrentIndex(idx)

    @property
    def baseClass(self):
        """
        must be implemented.
        """
        return None



class TemplateField(QtWidgets.QWidget):
    # TODO : implement this later
    def __init__(self, parent=None):
        super(TemplateField, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.chooser = ChooserField()
        layout.addWidget(self.chooser)
        self.refreshButton = QtWidgets.QPushButton("refresh")
        self.refreshButton.setFixedWidth(50)
        layout.addWidget(self.refreshButton)

    def getValue(self):
        return self.chooser.getValue()

    def setValue(self,value):
        self.chooser.setValue(value)

class OpInputField(AttrField, QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(OpInputField, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        label = QtWidgets.QLabel("block:")
        layout.addWidget(label)
        self.opField = QtWidgets.QLineEdit()
        layout.addWidget(self.opField)
        label = QtWidgets.QLabel("attr:")
        layout.addWidget(label)
        self.attrField = QtWidgets.QLineEdit()
        self.attrField.setText("results")
        layout.addWidget(self.attrField)

    def getValue(self):
        return self.opField.text(), self.attrField.text()

    def setValue(self, value):
        opVal, attrVal = value
        self.opField.setText(opVal)
        self.attrField.setText(attrVal)


class AttrTypeChooser(ChooserField):
    @property
    def items(self):
        return [(repr(atype), atype) for atype, field in AttrFieldMaker.fieldPairs]


class AttrFieldMaker(object):
    fieldPairs = ((str, StringField),
                  (int, IntField),
                  (float, FloatField),
                  (bool, BoolField),
                  (attrtype.Script, ScriptField),
                  (attrtype.Input, OpInputField),
    )

    defaultWidget = StringField

    attrMap = dict(fieldPairs)

    @classmethod
    def create(cls, attrType):
        attrFieldClass = cls.attrMap.get(attrType, cls.defaultWidget)
        return attrFieldClass()
