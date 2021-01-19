# -*- coding: utf-8 -*-
#
# This file is part of the parce-qt Python package.
#
# Copyright © 2020 by Wilbert Berendsen <info@wilbertberendsen.nl>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
The Python parceqt module provides parce parsing and highlighting
features for Qt's QTextDocument.

This module depends on the parce module.

With a few simple function calls you can highlight the syntax of
QTextDocument using parce.

"""

__all__ = (
    'Cursor',
    'Document',
    'Formatter',
    'TreeBuilder',
    'SyntaxHighlighter',
    'builder',
    'root',
    'set_root_lexicon',
    'root_lexicon',
    'highlight',
    'adjust_widget',
    'cursor',
    'version',
    'version_string',
)

from PyQt5.QtWidgets import QApplication

import parce.theme

from .pkginfo import version, version_string
from .document import Cursor, Document
from .formatter import Formatter
from .treebuilder import TreeBuilder
from .highlighter import SyntaxHighlighter


def builder(doc):
    """Return the TreeBuilder responsible for tokenizing this QTextDocument.

    If no TreeBuilder already existed, it is instantiated and becomes a child
    of the QTextDocument. You can connect to its ``updated()`` or ``changed()``
    signal to get notified of changes in the tokenized tree.

    """
    return TreeBuilder.instance(doc)


def root(doc, wait=False):
    """Get the root element of the tokenized tree of specified text document.

    See for more information about the arguments the ``get_root()`` method
    of ``treebuilder.TreeBuilder``.

    """
    return builder(doc).get_root(wait)


def set_root_lexicon(doc, lexicon):
    """Instatiate a TreeBuilder for the document if needed, and set its root lexicon."""
    builder(doc).set_root_lexicon(lexicon)


def root_lexicon(doc):
    """Return the currently active root lexicon for the QTextDocument."""
    return builder(doc).root_lexicon()


def highlight(doc, theme="default"):
    """Set the highlighting Theme for the document.

    Use a string value to select a Theme by name. Use None to disable
    highlighting, or use False to force the SyntaxHighlighter to quit.

    Of course, highlighting becomes only visible when the document has a
    root_lexicon set.

    """
    b = builder(doc)
    if theme is False:
        SyntaxHighlighter.delete_instance(b)
    else:
        if isinstance(theme, str):
            theme = parce.theme.Theme.byname(theme)
        formatter = Formatter(theme) if theme else None
        SyntaxHighlighter.instance(b).set_formatter(formatter)


def adjust_widget(widget):
    """Convenience function to set palette and font of a text editing ``widget``.

    Sets the widget's palette and font to the theme of its QTextDocument's
    highlighter.

    The widget must be a QPlainTextEdit, QTextEdit or QTextBrowser. If its
    document has not yet a theme set, this function does nothing.

    Basically this is as simple as::

        formatter = parceqt.formatter.Formatter(theme)
        widget.setFont(formatter.font())
        widget.setPalette(formatter.palette())

    but this function is useful when you just set the theme once to a document
    and want to have its editing widget adjusted.

    Also, when you stopped the highlighting, this function neatly switches the
    widget back to the default palette and font.

    """
    doc = widget.document()
    b = builder(doc)
    source = QApplication
    h = SyntaxHighlighter.get_instance(b)
    if h and h.formatter():
        source = h.formatter()
    widget.setFont(source.font(widget))
    widget.setPalette(source.palette(widget))


def cursor(cur):
    """Convenience function to return a Cursor for a Document that wraps a QTextDocument.

    You can alter the document via the parce.Document API.
    The returned Cursor has a textCursor() method that returns a QTextCursor
    for the same selection or position.

    """
    c = Cursor(Document(cur.document()))
    c.pos = cur.selectionStart()
    c.end = cur.selectionEnd()
    return c


