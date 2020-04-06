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
This module provides a SyntaxHighlighter.
"""

from PyQt5.QtCore import QEventLoop, QObject, Qt
from PyQt5.QtGui import QGuiApplication, QTextCharFormat, QTextCursor, QTextLayout

import parce.util
import parce.theme

from . import treebuilder
from . import util
from . import formatter


class SyntaxHighlighter(util.SingleInstance):
    """Provides syntax highlighting using parce parsers.

    Instantiate with::

        SyntaxHighlighter.instance(treebuilder)

    Use the builder to set the root lexicon.

    By default, no theme is set; use ``set_theme()`` to set a theme, which is
    needed to enable highlighting.

    """
    def __init__(self, builder):
        self._formatter = None
        self._cursor = None      # remembers the range to rehighlight
        builder.updated.connect(self.slot_updated)
        builder.changed.connect(self.slot_changed)
        builder.preview.connect(self.slot_preview, Qt.BlockingQueuedConnection)

    def builder(self):
        """Return the builder we were instantiated with."""
        return self.target_object()

    def delete(self):
        """Reimplemented to clear the highlighting before delete."""
        self.clear()
        super().delete()

    def set_theme(self, theme):
        """Set the Theme to use. The Theme provides the text formats to highlight.

        If you set the theme to None, highlighting is effectively disabled,
        although the TreeBuilder still does the tokenizing.

        """
        if theme is not self.theme():
            self._formatter = formatter.Formatter(theme) if theme else None
            self.rehighlight() if theme else self.clear()

    def theme(self):
        """Return the currently set Theme."""
        if self._formatter:
            return self._formatter.theme()

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
        return self.builder().document()

    def slot_changed(self, start, offset):
        """Called on small changes, allows for moving the formats, awaiting the tokenizer."""
        doc = self.document()
        block = doc.findBlock(start)
        start -= block.position()
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
                if r.start <= start:
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

    def slot_preview(self, tree):
        """Called when there is a peek preview."""
        print("peek from highlighter")
        tree.dump()

    def slot_updated(self, start, end):
        """Called on update; performs the highlighting."""
        formatter = self._formatter
        if not formatter:
            return
        doc = self.document()

        c = self._cursor
        if c:
            # our previous highlighting run was interrupted, fix it now
            start = min(start, c.selectionStart())
            end = max(end, c.selectionEnd())
        else:
            c = self._cursor = QTextCursor(doc)
            c.setKeepPositionOnInsert(True)

        block = doc.findBlock(start)
        start = pos = block.position()
        last_block = doc.findBlock(end)
        if not last_block.isValid():
            last_block = doc.lastBlock()
        end = last_block.position() + last_block.length() - 1

        c.setPosition(end)

        num = block.blockNumber() + 100
        formats = []
        root = self.builder().root
        for f in formatter.format_ranges(root.context_slices(start, end)):
            while f.pos >= pos + block.length():
                block.layout().setFormats(formats)
                block = block.next()
                pos = block.position()
                formats = []
            r = QTextLayout.FormatRange()
            r.format = f.textformat
            r.start = f.pos - pos
            f_end = min(end, f.end)
            while f_end > pos + block.length():
                r.length = block.length() - r.start - 1
                formats.append(r)
                block.layout().setFormats(formats)
                block = block.next()
                pos = block.position()
                formats = []
                r = QTextLayout.FormatRange()
                r.format = f.textformat
                r.start = 0
            r.length = f_end - pos - r.start
            formats.append(r)
            if block.blockNumber() > num:
                num = block.blockNumber() + 1000
                doc.markContentsDirty(start, pos - start)
                start = pos
                c.setPosition(start, QTextCursor.KeepAnchor)
                revision = doc.revision()
                QGuiApplication.processEvents(QEventLoop.ExcludeSocketNotifiers)
                # if the user typed, immediately quit, but come back!
                if doc.revision() != revision:
                    return
        block.layout().setFormats(formats)
        while block < last_block:
            block = block.next()
            block.layout().clearFormats()
        doc.markContentsDirty(start, end - start)
        # we have finished highlighting
        self._cursor = None


def split_formats(block, position):
    """Return two lists of FormatRange instances from the block's layout.

    The first are the formats from the start of the block until position (which
    must be inside the block). The second are the formats from the position
    to the end of the block, shifted as if the block started at position.

    A format range is neatly cut in two when position lies in the middle of
    a range.

    """
    def new_format_range(r, offset=0):
        n = QTextLayout.FormatRange()
        n.format = r.format
        n.start = r.start + offset
        n.length = r.length
        return n
    pos = position - block.position()
    formats = iter(block.layout().formats())
    start_formats = []
    end_formats = []
    for r in formats:
        if r.start < pos:
            n = new_format_range(r)
            start_formats.append(n)
            if r.start + r.length > pos:
                n.length = pos - r.start
                n = new_format_range(r)
                n.start = 0
                n.length = r.start + r.length - pos
                end_formats.append(n)
                break
        else:
            n = new_format_range(r, -pos)
            end_formats.append(n)
            break
    for r in formats:
        n = new_format_range(r, -pos)
        end_formats.append(n)
    return start_formats, end_formats


