import json
import ast
from qqt import QtCore, QtWidgets, QtGui
from qqt.gui import qcreate, HBoxLayout, VBoxLayout, Button
from brick import attr_type
from brick.ui import IconManager
from brick.ui.components.script_editor import ScriptEditor
from brick.lib import classproperty
from brick.lib.path import Path
from collections import OrderedDict


class AttrField(object):
    editFinished = QtCore.Signal()

    @property
    def sizePolicy(self):
        return QtCore.QSizePolicy(QtCore.QSizePolicy.Preferred, QtCore.QSizePolicy.Fixed)

    def emitSignal(self):
        self.editFinished.emit()


class StringField(AttrField, QtWidgets.QLineEdit):
    attrType = attr_type.String

    def __init__(self, parent=None):
        super(StringField, self).__init__(parent)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        self.setText(str(value))

    def getValue(self):
        return self.text()


class IntField(AttrField, QtWidgets.QLineEdit):
    attrType = attr_type.Int

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
    attrType = attr_type.Bool

    True_ = str(True)
    False_ = str(False)

    def __init__(self, parent=None):
        super(BoolField, self).__init__(parent)
        self.setMaximumWidth(90)
        self.editingFinished.connect(self.convertValue)
        self.editingFinished.connect(self.emitSignal)

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


class FloatField(AttrField, QtWidgets.QLineEdit):
    attrType = attr_type.Float

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


class ListField(AttrField, QtWidgets.QLineEdit):
    attrType = attr_type.List

    def __init__(self, parent=None):
        super(ListField, self).__init__(parent)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        if not value:
            strVal = ""
        elif isinstance(value,(list, tuple)):
            strVal = json.dumps(value)
        else:
            strVal = value

        self.setText(strVal)

    def getValue(self):
        text = self.text()

        if not text:
            val = []
        else:
            val = ast.literal_eval(text)

        return val


class DictField(AttrField, QtWidgets.QLineEdit):
    attrType = attr_type.Dict

    def __init__(self, parent=None):
        super(DictField, self).__init__(parent)
        self.editingFinished.connect(self.emitSignal)

    def setValue(self, value):
        if not value:
            strVal = ""
        elif isinstance(value, (dict, OrderedDict)):
            strVal = json.dumps(value)
        else:
            strVal = value

        self.setText(strVal)

    def getValue(self):
        text = self.text()

        if not text:
            val = OrderedDict()
        else:
            val = ast.literal_eval(text)

        return val


class ChooserField(AttrField, QtWidgets.QComboBox):
    attrType = attr_type.Chooser

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


class ScriptField(AttrField, QtWidgets.QWidget):
    attrType = attr_type.Script

    def __init__(self, parent=None):
        super(ScriptField, self).__init__(parent)
        layout = HBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        with layout:
            self.scriptField = qcreate(QtWidgets.QLineEdit)
            self.scriptField.setEnabled(False)
            self.editButton = qcreate(Button, "edit")
        self.editButton.clicked.connect(self.openScriptEditor)

    def setValue(self, value):
        setVal = attr_type.Script(value.replace('\n', r'\n'))
        self.scriptField.setText(setVal)

    def openScriptEditor(self):
        currentScript = self.scriptField.text()
        convertedScript = attr_type.Script(currentScript.replace(r'\n', '\n'))
        self._sui = ScriptEditor(script=convertedScript)
        self._sui.scriptAccepted.connect(self.scriptAcceptedCallback)
        self._sui.show()

    def scriptAcceptedCallback(self, script):
        self.scriptField.setText(script)
        self.emitSignal()

    def getValue(self):
        val = self.scriptField.text()
        return attr_type.Script(val.replace(r'\n', '\n'))


class PathField(AttrField, QtWidgets.QWidget):
    attrType = attr_type.Path

    def __init__(self, parent=None):
        super(PathField, self).__init__(parent)
        layout = HBoxLayout(self)
        with layout:
            self.scriptField = qcreate(QtWidgets.QLineEdit)
            self.scriptField.editingFinished.connect(self.emitSignal)
            self.editButton = qcreate(Button, "browse")
        self.editButton.clicked.connect(self.openFileDialog)

    def setValue(self, value):
        value = Path(value)
        self.scriptField.setText(value.normcase())

    def openFileDialog(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName()

        if fileName:
            self.setValue(fileName[0])
            self.emitSignal()

    def getValue(self):
        val = self.scriptField.text()
        return unicode(val)


class NamedObjectField(AttrField, QtWidgets.QWidget):
    attrType = attr_type.NamedObject

    def __init__(self, parent=None):
        super(NamedObjectField, self).__init__(parent)
        layout = HBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        with layout:
            self.scriptField = qcreate(QtWidgets.QLineEdit)
            self.scriptField.setEnabled(False)
            self.editButton = qcreate(Button, "edit")
        self.editButton.clicked.connect(self.openScriptEditor)

    def setValue(self, value):
        setVal = attr_type.Script(value.replace('\n', r'\n'))
        self.scriptField.setText(setVal)

    def openScriptEditor(self):
        currentScript = self.scriptField.text()
        convertedScript = attr_type.Script(currentScript.replace(r'\n', '\n'))
        self._sui = ScriptEditor(script=convertedScript)
        self._sui.scriptAccepted.connect(self.scriptAcceptedCallback)
        self._sui.show()

    def scriptAcceptedCallback(self, script):
        self.scriptField.setText(script)
        self.emitSignal()

    def getValue(self):
        val = self.scriptField.text()
        return attr_type.Script(val.replace(r'\n', '\n'))


class BlockInputField(AttrField, QtWidgets.QWidget):
    attrType = attr_type.Input

    def __init__(self, parent=None):
        super(BlockInputField, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        label = QtWidgets.QLabel("block:")
        layout.addWidget(label)
        self.blockField = QtWidgets.QLineEdit()
        layout.addWidget(self.blockField)
        self.blockField.editingFinished.connect(self.emitSignal)

        label = QtWidgets.QLabel("attr:")
        layout.addWidget(label)
        self.attrField = QtWidgets.QLineEdit()
        self.attrField.setText("results")
        self.attrField.editingFinished.connect(self.emitSignal)

        layout.addWidget(self.attrField)

    def getValue(self):
        return self.blockField.text(), self.attrField.text()

    def setValue(self, value):
        opVal, attrVal = value
        self.blockField.setText(opVal)
        self.attrField.setText(attrVal)


class AttrTypeChooser(ChooserField):
    attrType = attr_type.TypeChosser

    @property
    def items(self):
        return AttrFieldMaker.fields

    def reloadItems(self):
        while self.count() > 0:
            for idx in range(self.count()):
                self.removeItem(idx)

        for field in self.items:
            self.addItem(str(field.attrType.__name__), userData=field)


class AttrFieldMaker(object):
    fields = (StringField, IntField, FloatField, BoolField, ListField, DictField, ScriptField, PathField, NamedObjectField, BlockInputField)

    defaultWidget = StringField

    @classproperty
    def attrMap(cls):
        amap = OrderedDict()
        for each in cls.fields:
            amap[each.attrType] = each
        return amap

    @classmethod
    def create(cls, attrType):

        attrFieldClass = cls.attrMap.get(attrType)

        if not attrFieldClass:
            raise ValueError("attrFieldClass not found.")
        return attrFieldClass()
