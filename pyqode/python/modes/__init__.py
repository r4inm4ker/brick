# -*- coding: utf-8 -*-
"""
This package contains a series of python specific modes (calltips,
autoindent, code linting,...).

"""
from .autocomplete import PyAutoCompleteMode
from .autoindent import PyAutoIndentMode
from .comments import CommentsMode
from .indenter import PyIndenterMode


try:
    # load pyqode.python resources (code completion icons)
    from pyqode.python._forms import pyqode_python_icons_rc  # DO NOT REMOVE!!!
except ImportError:
    # PyQt/PySide might not be available for the interpreter that run the
    # backend
    pass


__all__ = [
    'CommentsMode',
    'PyAutoCompleteMode',
    'PyAutoIndentMode',
    'PyIndenterMode',
]
