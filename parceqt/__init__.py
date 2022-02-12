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
The Python *parceqt* module provides *parce* parsing and highlighting
features for Qt's QTextDocument.

This module depends on the :mod:`parce` module.

With a few simple function calls you can highlight the syntax of a
QTextDocument using parce.

Besides the functions below, the following classes and values are also
accessible in this module scope:
:class:`~.document.Cursor`,
:class:`~.document.Document`,
:class:`~.formatter.Formatter`,
:class:`~.highlighter.SyntaxHighlighter`,
:data:`~.pkginfo.version`,
:data:`~.pkginfo.version_string`.

"""

from PyQt5.QtWidgets import QApplication

import parce

from .pkginfo import version, version_string
from .document import Cursor, Document
from .formatter import Formatter
from .highlighter import SyntaxHighlighter


def worker(doc):
    """Return the :class:`~.work.Worker` responsible for tokenizing this
    QTextDocument.

    If no Worker already existed, it is instantiated and becomes a child of the
    QTextDocument. You can connect to its signals to get notified of changes in
    the tokenized tree or transformed result.

    """
    from . import work
    return work.Worker.instance(doc)


def root(doc, wait=False):
    """Get the root element of the tokenized tree of specified text document.

    See for more information about the arguments the
    :meth:`~.treebuilder.TreeBuilder.get_root` method of
    :class:`~.treebuilder.TreeBuilder`.

    """
    return worker(doc).get_root(wait)


def set_root_lexicon(doc, lexicon):
    """Instatiate a Worker for the document if needed, and set its root lexicon."""
    Document(doc).set_root_lexicon(lexicon)


def root_lexicon(doc):
    """Return the currently active root lexicon for the QTextDocument."""
    return worker(doc).builder().root.lexicon


def highlight(doc, theme="default"):
    """Set the highlighting Theme for the document.

    Use a string value to select a Theme by name. Use None to disable
    highlighting, or use False to force the SyntaxHighlighter to quit.

    Of course, highlighting becomes only visible when the document has a
    root_lexicon set.

    """
    if isinstance(theme, str):
        theme = parce.theme_by_name(theme)
    formatter = Formatter(theme) if theme else theme
    Document(doc).set_formatter(formatter)


def adjust_widget(widget):
    """Convenience function to set palette and font of a text editing ``widget``.

    Sets the widget's palette and font to the theme of its QTextDocument's
    highlighter.

    The widget must be a QPlainTextEdit, QTextEdit or QTextBrowser. If its
    document has not yet a theme set, this function does nothing.

    Basically this is as simple as::

        formatter = parceqt.Formatter(theme)
        widget.setFont(formatter.font())
        widget.setPalette(formatter.palette())

    but this function is useful when you just set the theme once to a document
    and want to have its editing widget adjusted.

    Also, when you stopped the highlighting, this function neatly switches the
    widget back to the default palette and font.

    """
    doc = widget.document()
    source = Document(doc).formatter() or QApplication
    widget.setFont(source.font(widget))
    widget.setPalette(source.palette(widget))


def cursor(cursor):
    """Convenience function to return a :class:`~.document.Cursor` with a
    :class:`~.document.Document` that wraps a QTextDocument.

    The specified ``cursor`` must be a QTextCursor. You can alter the document
    via the parce.Document API.

    """
    return Cursor(Document(cursor.document()), cursor.selectionStart(), cursor.selectionEnd())


