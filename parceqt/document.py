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
This module implements a Document encapsulating a QTextDocument.

It is not needed to store the Document itself, it is only used
to modify the QTextDocument through the parce.Document API.

We do not ourself retokenize the text, that is done by a TreeBuilder
that is automatically connected to the document.

"""

from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QTextCursor, QTextDocument
from PyQt5.QtWidgets import QApplication

import parce.document

from . import treebuilder, work, highlighter


class Document(parce.DocumentInterface):
    """Document accesses a QTextDocument via the parce.Document API.

    There are two ways to construct a Document, and both use the default
    constructor. The first and default way is calling the constructor with the
    same arguments as the :class:`parce.Document` constructor. This way a
    QTextDocument is created as well, containing the text. Only that
    QTextDocument actually needs to be kept; there is no need to store the
    Document object, it is only used to access and modify the contents of a
    QTextDocument. An example::

        >>> d = parceqt.Document(MyLang.root, "text")
        >>> d.document()
        <PyQt5.QtGui.QTextDocument object at 0x7f6706473c10>

    The second way is to call the constructor with the QTextDocument as the
    first argument. This creates also a new Document instance, but it wraps the
    existing QTextDocument, so that it can be accessed (again) via the *parce*
    API.

        >>> d = Document(doc)   # where doc is an existing QTextDocument
        >>> with d:
        ...     d[5:5] = 'some text'

    This is useful when you have written code that manipulates text files based
    on the tokenized tree via the parce.Document API, you can use the same code
    to manipulate QTextDocuments, e.g. in a GUI editor.

    Just like with parce.Document, updating the token tree (and the transformed
    result) is handled by a Worker, which in ``parceqt`` is a QObject that
    lives as long as the QTextDocument, in the background, as a child of it.

    The ``url`` property is stored in the QTextDocument's meta information;
    the ``encoding`` property is currently not retained when a Document is
    instantiated again.

    It is not necessary to supply a ``worker``, because in *parceqt* the
    :class:`~parceqt.work.Worker` is a child object of the QTextDocument and
    instantiated automatically by this constructor.



    """
    def __init__(self, root_lexicon=None, text="", url=None, encoding=None, worker=None, transformer=None):
        if isinstance(root_lexicon, QTextDocument):
            # we wrap an existing QTextDocument
            doc = root_lexicon
            root_lexicon = text = None
        else:
            doc = QTextDocument(text)
            doc.setModified(False)
        self._document = doc
        if not worker:
            worker = work.Worker.instance(doc)
        super().__init__(root_lexicon, text, url, encoding, worker, transformer)

    def set_formatter(self, formatter):
        """Set a :class:`~parceqt.formatter.Formatter` to enable syntax highlighting.

        If ``formatter`` is None, highlighting is effectively disabled. If
        False, the :class:`~parceqt.highlighter.SyntaxHighlighter` is deleted
        if active.

        Example::

            >>> import parce
            >>> import parceqt
            >>> # of course create QApplication etc...
            >>> f = parceqt.Formatter(parce.theme_by_name('default'))
            >>> d = parceqt.Document.load("my_file.css")
            >>> d.set_formatter(f)

        The same Formatter can be used for multiple documents.

        """
        if formatter is False:
            highlighter.SyntaxHighlighter.delete_instance(self.worker())
        elif formatter:
            highlighter.SyntaxHighlighter.instance(self.worker()).set_formatter(formatter)
        else:
            h = highlighter.SyntaxHighlighter.get_instance(self.worker())
            if h:
                h.set_formatter(None)

    def formatter(self, formatter):
        """Return the :class:`~parceqt.formatter.Formatter` that is used for syntax highlighting.

        Returns None if no formatter was set.

        """
        h = highlighter.SyntaxHighlighter.get_instance(self.worker())
        if h:
            return h.formatter()

    @property
    def url(self):
        """The url of this document, stored in QTextDocument's meta information."""
        return self._document.metaInformation(QTextDocument.DocumentUrl)

    @url.setter
    def url(self, url):
        self._document.setMetaInformation(QTextDocument.DocumentUrl, url)

    @url.deleter
    def url(self):
        self._document.setMetaInformation(QTextDocument.DocumentUrl, "")

    @property
    def revision(self):
        """The QTextDocument's revision."""
        return self._document.revision()

    @property
    def modified(self):
        """Whether the QTextDocument is modified."""
        return self._document.isModified()

    @modified.setter
    def modified(self, modified):
        self._document.setModified(modified)

    def document(self):
        """Return our QTextDocument."""
        return self._document

    def text(self):
        """Reimplemented to get the text from the QTextDocument."""
        return self.document().toPlainText()

    def __len__(self):
        """Reimplemented to return the length of the text in the QTextDocument."""
        # see https://bugreports.qt.io/browse/QTBUG-4841
        return self.document().characterCount() - 1

    def _update_text(self, changes):
        """Apply the changes to our QTextDocument."""
        c = QTextCursor(self.document())
        c.beginEditBlock()
        for start, end, text in reversed(changes):
            c.setPosition(end)
            if start != end:
                c.setPosition(start, QTextCursor.KeepAnchor)
            c.insertText(text)
        c.endEditBlock()

    def _get_text(self, start, end):
        """Reimplemented to get a fragment of our text.

        This is faster than getting the whole text and using Python to slice it.

        """
        c = QTextCursor(self.document())
        c.setPosition(end)
        c.setPosition(start, QTextCursor.KeepAnchor)
        return c.selection().toPlainText()

    def text_changed(self, start, removed, added):
        """Reimplemented to do nothing, it is already handled by TreeBuilder."""
        pass

    def find_start_of_block(self, position):
        """Reimplemented to use QTextDocument's TextBlock."""
        block = self.document().findBlock(position)
        if not block.isValid():
            block = self.document().lastBlock()
        return block.position()

    def find_end_of_block(self, position):
        """Reimplemented to use QTextDocument's TextBlock."""
        block = self.document().findBlock(position)
        if not block.isValid():
            block = self.document().lastBlock()
        return block.position() + block.length() - 1


class Cursor(parce.document.Cursor):
    """A cursor with a textCursor() method to return a QTextCursor.

    Only use this Cursor with parceqt.Document.

    """
    def textCursor(self):
        """Return a QTextCursor for our document with the same position and
        selection.

        (This method uses the Qt camelCase naming convention.)

        """
        c = QTextCursor(self.document().document())
        if self.end is None:
            c.movePosition(QTextCursor.End)
        else:
            c.setPosition(self.end)
        c.setPosition(self.start, QTextCursor.KeepAnchor)
        return c

    def html(self):
        """Return the selected range as HTML.

        Uses the same theme(s) as the highlighter (if active).

        """
        from . import highlighter, treebuilder
        from parce.out.html import HtmlFormatter
        formatter = HtmlFormatter()
        b = treebuilder.TreeBuilder.get_instance(self.document().document())
        if b:
            h = highlighter.SyntaxHighlighter.get_instance(b)
            if h and h.formatter():
                formatter.copy_themes(h.formatter())
        return formatter.full_html(self)

    def copy_html(self):
        """Copy the selected range as HTML to the Qt clipboard."""
        data = QMimeData()
        data.setHtml(self.html())
        QApplication.clipboard().setMimeData(data)


