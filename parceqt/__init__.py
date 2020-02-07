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

from .pkginfo import version, version_string
from .document import Document


def builder(doc):
    """Return the TreeBuilder responsible for tokenizing this QTextDocument.

    If no TreeBuilder already existed, it is instantiated and becomes a child
    of the QTextDocument. You can connect to its ``updated()`` or ``changed()``
    signal to get notified of changes in the tokenized tree.

    """
    from . import treebuilder
    return treebuilder.TreeBuilder.instance(doc)

def root(doc, wait=False, callback=None, args=None, kwargs=None):
    """Get the root element of the tokenized tree of specified text document.

    See for more information about the arguments the ``get_root()`` method
    of ``parce.treebuilder.BackgroundTreeBuilder``.

    """
    return builder(doc).get_root(wait, callback, args, kwargs)


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
    from . import highlighter
    if theme is False:
        highlighter.SyntaxHighlighter.delete_instance(doc)
    else:
        if isinstance(theme, str):
            from .theme import Theme
            theme = Theme.byname(theme)
        highlighter.SyntaxHighlighter.instance(doc).set_theme(theme)

