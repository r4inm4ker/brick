# -*- coding: utf-8 -*-
"""
This package contains a set of widgets that might be useful when writing
pyqode applications:

    - TextCodeEdit: code edit specialised for plain text
    - GenericCodeEdit: generic code edit, using PygmentsSH.
      Not really fast, not really smart.
    - InteractiveConsole: QTextEdit made for running background process
      interactively. Can be used in an IDE for running programs or to display
      the compiler output,...
    - CodeEditTabWidget: tab widget made to handle CodeEdit instances (or
      any other object that have the same interface).
    - ErrorsTable: a QTableWidget specialised to show CheckerMessage.
    - OutlineTreeWidget: a widget that show the outline of an editor.


"""
from pyqode.core.widgets.code_edits import TextCodeEdit, GenericCodeEdit
from pyqode.core.widgets.encodings import (EncodingsComboBox, EncodingsMenu,
                                           EncodingsContextMenu)

from pyqode.core.widgets.menu_recents import MenuRecentFiles
from pyqode.core.widgets.menu_recents import RecentFilesManager
from pyqode.core.widgets.preview import HtmlPreviewWidget

from pyqode.core.widgets.tab_bar import TabBar
from pyqode.core.widgets.prompt_line_edit import PromptLineEdit
from pyqode.core.widgets.outline import OutlineTreeWidget
from pyqode.core.widgets.splittable_tab_widget import (
    SplittableTabWidget, SplittableCodeEditTabWidget)


__all__ = [
    'MenuRecentFiles',
    'RecentFilesManager',
    'EncodingsComboBox',
    'EncodingsMenu',
    'EncodingsContextMenu',
    'TextCodeEdit',
    'GenericCodeEdit',
    'PromptLineEdit',
    'OutlineTreeWidget',
    'SplittableTabWidget',
    'SplittableCodeEditTabWidget',
    'TabBar',
    'HtmlPreviewWidget',

]
