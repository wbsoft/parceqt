# -*- coding: utf-8 -*-
#
# This file is part of the livelex-qt Python package.
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
This module implements a SyntaxHighlighter.


"""

import weakref

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QTextCharFormat, QTextLayout

import livelex.util

from . import treebuilder


class SyntaxHighlighter:
    """Provides syntax highlighting using livelex parsers.

    Inherit, implement get_format() and instantiate with:

        MyHighlighter.instance(qTextDocument, root_lexicon)

    """

    @classmethod
    def instance(cls, document):
        """Get or create the SyntaxHighlighter instance for the QTextDocument."""
        try:
            return cls._instances[document]
        except AttributeError:
            cls._instances = weakref.WeakKeyDictionary()
        except KeyError:
            pass
        new = cls._instances[document] = cls(document)
        return new

    def __init__(self, document):
        self._document = document
        builder = treebuilder.TreeBuilder.instance(document)
        builder.updated.connect(self.slot_updated)
        if builder.get_root():
            self.slot_updated(0, document.characterCount() - 1)

    def clear(self):
        """Clear the highlighting. Do this before deleting."""
        doc = self.document()
        block = doc.firstBlock()
        while block.isValid():
            block.layout().clearFormats()
            block = block.next()
        doc.markContentsDirty(0, doc.characterCount() - 1)

    def document(self):
        """Return the QTextDocument."""
        return self._document

    def root_lexicon(self):
        """Return the currently (being) set root lexicon."""
        builder = treebuilder.TreeBuilder.instance(self.document())
        return builder.root_lexicon()

    def set_root_lexicon(self, root_lexicon):
        """Set the root lexicon to use to tokenize the text. Triggers a rebuild."""
        builder = treebuilder.TreeBuilder.instance(self.document())
        builder.set_root_lexicon(root_lexicon)

    def slot_updated(self, start, end):
        """Called on update; performs the highlighting."""
        doc = self.document()
        block = doc.findBlock(start)
        start = pos = block.position()
        last_block = self.document().findBlock(end)
        end = last_block.position() + last_block.length() - 1
        formats = []
        root = treebuilder.TreeBuilder.instance(self.document()).root
        for t_pos, t_end, action in livelex.util.merge_adjacent_actions(
                root.tokens_range(start, end)):
            while t_pos >= pos + block.length():
                block.layout().setFormats(formats)
                block = block.next()
                pos = block.position()
                formats = []
            r = QTextLayout.FormatRange()
            r.format = f = self.get_format(action)
            r.start = t_pos - pos
            t_end = min(end, t_end)
            while t_end > pos + block.length():
                r.length = block.length() - r.start - 1
                formats.append(r)
                block.layout().setFormats(formats)
                block = block.next()
                pos = block.position()
                formats = []
                r = QTextLayout.FormatRange()
                r.format = f
                r.start = 0
            r.length = t_end - pos - r.start
            formats.append(r)
        block.layout().setFormats(formats)
        while block < last_block:
            block = block.next()
            block.layout().clearFormats()
        doc.markContentsDirty(start, end - start)

    def get_format(self, action):
        """Implement this method to return a QTextCharFormat for the action."""
        ### TEMP!
        from PyQt5.QtGui import QFont
        f = QTextCharFormat()
        if action in livelex.String:
            f.setForeground(Qt.red)
        elif action in livelex.Name:
            f.setForeground(Qt.blue)
        if action in livelex.Comment:
            f.setForeground(Qt.darkGray)
            f.setFontItalic(True)
        if action in livelex.Delimiter:
            f.setFontWeight(QFont.Bold)
        if action in livelex.Escape:
            f.setForeground(Qt.darkGreen)
        return f

