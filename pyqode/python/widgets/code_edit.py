# -*- coding: utf-8 -*-
"""
This package contains the python code editor widget
"""

from pyqode.core import api
from pyqode.python import managers as pymanagers


class PyCodeEditBase(api.CodeEdit):
    """
    Base class for creating a python code editor widget. The base class
    takes care of setting up the syntax highlighter.

    .. note:: This code editor widget use PEP 0263 to detect file encoding.
              If the opened file does not respects the PEP 0263,
              :py:func:`locale.getpreferredencoding` is used as the default
              encoding.
    """

    def __init__(self, parent=None, create_default_actions=True):
        super(PyCodeEditBase, self).__init__(parent, create_default_actions)
        self.file = pymanagers.PyFileManager(self)

    def setPlainText(self, txt, mimetype='text/x-python', encoding='utf-8'):
        """
        Extends QCodeEdit.setPlainText to allow user to setPlainText without
        mimetype (since the python syntax highlighter does not use it).
        """
        try:
            self.syntax_highlighter.docstrings[:] = []
            self.syntax_highlighter.import_statements[:] = []
        except AttributeError:
            pass
        super(PyCodeEditBase, self).setPlainText(txt, mimetype, encoding)
