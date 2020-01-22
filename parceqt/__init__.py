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

The following classes are provided: TreeBuilder, Document and
SyntaxHighlighter. The module's version is available through the version (a
tuple) and version_string variables.


TreeBuilder
-----------

The TreeBuilder inherits parce.BackgroundTreeBuilder, but uses a Qt
QThread to build the tree of tokens in the background, emitting an updated()
signal when the tree is ready. The TreeBuilder is a QObject itself, and
becomes the child of the QTextDocument it keeps tokenized.

The following code gets a TreeBuilder for a textdocument, creating it if
necessary:

    builder = TreeBuilder.instance(qtextdocument)

You can set the root lexicon with:

    builder.set_root_lexicon(MyLang.root)

This method call will immediately return, a background thread will be started
to retokenize the document. (If a tokenizing process was already busy, it
immediately adapts to the current change.)

To get the tree, use builder.get_root(). If this returns None, tokenizing is
still busy. Use get_root(True) to wait, or get_root(callback=my_callback) to
be notified.

Document
--------

The Document just implements parce.TreeDocument around a QTextDocument. You
do not need to store the Document, you can just use it to manipulate the
QTextDocument through the parce.AbstractDocument API. You can also get
the tree of tokens, which is created and kept by the TreeBuilder.

Use it like this:

    with Document(qtextdocument) as d:
        d[20:30] = "new text"
        # etc

After leaving the context, the changes are applied to the QTextDocument,
and you can safely let the Document being garbage collected.


SyntaxHighlighter
-----------------

The SyntaxHighlighter can live on its own and connects to the updated()
signal of the TreeBuilder and highlights the text in the QTextDocument.
Currently, you need to inherit from it and implement the get_format()
method, which should return a QTextFormat for the specified action.

Usage:

    class MyHighlighter(SyntaxHighlighter):
        def get_format(self, action):
            # whatever it takes to return a QTextFormat
            return some_QTextFormat[action]

    MyHighlighter.instance(qtextdocument)

The SyntaxHighlighter is a QObject which becomes a child of the QTextDocument
as well. To stop the highlighting, call:

    MyHighlighter.delete_instance(qtextdocument)

or:

    MyHighlighter.instance(qtextdocument).delete()

"""

from .pkginfo import version, version_string

from .treebuilder import TreeBuilder
from .document import Document
from .highlighter import SyntaxHighlighter

