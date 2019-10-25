# -*- coding: utf-8 -*-
"""
This package contains the core modes.

"""
from .autocomplete import AutoCompleteMode
from .autoindent import AutoIndentMode
from .backspace import SmartBackSpaceMode
from .caret_line_highlight import CaretLineHighlighterMode
from .case_converter import CaseConverterMode
from .cursor_history import CursorHistoryMode
from .code_completion import CodeCompletionMode
from .extended_selection import ExtendedSelectionMode
from .indenter import IndenterMode
from .line_highlighter import LineHighlighterMode
from .matcher import SymbolMatcherMode
from .occurences import OccurrencesHighlighterMode
from .outline import OutlineMode
from .right_margin import RightMarginMode
from .wordclick import WordClickMode
from .zoom import ZoomMode
# for backward compatibility


__all__ = [
    'AutoCompleteMode',
    'AutoIndentMode',
    'CaretLineHighlighterMode',
    'CaseConverterMode',
    'CodeCompletionMode',
    'CursorHistoryMode',
    'ExtendedSelectionMode',
    'IndenterMode',
    'LineHighlighterMode',
    'OccurrencesHighlighterMode',
    'OutlineMode',
    'RightMarginMode',
    'SmartBackSpaceMode',
    'SymbolMatcherMode',
    'WordClickMode',
    'ZoomMode',
]
