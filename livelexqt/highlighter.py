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
from . import util


class SyntaxHighlighter(util.SingleInstance):
    """Provides syntax highlighting using livelex parsers.

    Inherit, implement get_format() and instantiate with:

        MyHighlighter.instance(qTextDocument, root_lexicon)

    """
    def __init__(self, document, default_root_lexicon=None):
        builder = treebuilder.TreeBuilder.instance(document, default_root_lexicon)
        builder.updated.connect(self.slot_updated)
        builder.changed.connect(self.slot_changed)
        if builder.get_root():
            self.rehighlight()

    def delete(self):
        """Reimplemented to clear the highlighting before delete."""
        self.clear()
        super().delete()

    def clear(self):
        """Clear the highlighting. Do this before deleting."""
        doc = self.document()
        block = doc.firstBlock()
        while block.isValid():
            block.layout().clearFormats()
            block = block.next()
        doc.markContentsDirty(0, doc.characterCount() - 1)

    def rehighlight(self):
        """Draws the highlighting again. Normally not needed."""
        self.slot_updated(0, self.document().characterCount() - 1)

    def document(self):
        """Return the QTextDocument."""
        return self.target_object()

    def root_lexicon(self):
        """Return the currently (being) set root lexicon."""
        builder = treebuilder.TreeBuilder.instance(self.document())
        return builder.root_lexicon()

    def set_root_lexicon(self, root_lexicon):
        """Set the root lexicon to use to tokenize the text. Triggers a rebuild."""
        builder = treebuilder.TreeBuilder.instance(self.document())
        builder.set_root_lexicon(root_lexicon)

    def slot_changed(self, start, offset):
        """Called on small changes, allows for moving the formats, awaiting the tokenizer."""
        doc = self.document()
        block = doc.findBlock(start)
        formats = block.layout().formats()
        i = 0
        hi = len(formats)
        while i < hi:
            mid = (i + hi) // 2
            r = formats[mid]
            if r.start + r.length <= start:
                i = mid + 1
            else:
                hi = mid
        if i < len(formats):
            r = formats[i]
            if offset == 0:
                if r.start < start:
                    del formats[i+1:]
                else:
                    del formats[i:]
            else:
                if r.start < start:
                    # overlap
                    r.length = max(start - r.start, r.length + offset)
                    i += 1
                for r in formats[i:]:
                    # move whole format
                    r.start += offset
                    if r.start < start:
                        r.length -= start - r.start
                        r.start = start
            block.layout().setFormats(formats)

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

