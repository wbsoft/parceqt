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
ExtraSelectionManager managages highlighting of arbitrary sections in a
Q(Plain)TextEdit.
"""

import operator
import weakref

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTextEdit

from ..util import SingleInstance


class ExtraSelectionManager(SingleInstance):
    """Manages highlighting of arbitrary sections in a Q(Plain)TextEdit.

    Stores and highlights lists of QTextCursors on a per-format basis.

    Instantiate with::

        ExtraSelectionManager.instance(textedit)

    This ensures you get the same instance each time, and only one instance
    is created.

    """
    def __init__(self, textedit):
        super().__init__(textedit)
        self._selections = {}
        self._formats = {} # store the QTextFormats

    def highlight(self, text_format, cursors, priority=0, msec=0):
        """Highlight the selection of an arbitrary list of QTextCursors.

        ``text_format`` is a QTextCharFormat; ``priority`` determines the order
        of drawing, highlighting with higher priority is drawn over
        highlighting with lower priority. ``msec``, if > 0, removes the
        highlighting after that many milliseconds.

        """
        key = id(text_format)
        self._formats[key] = text_format
        selections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format = text_format
            selections.append(es)
        if msec:
            def clear(selfref=weakref.ref(self)):
                self = selfref()
                if self:
                    self.clear(text_format)
            timer = QTimer(timeout=clear, singleShot=True)
            timer.start(msec)
            self._selections[key] = (priority, selections, timer)
        else:
            self._selections[key] = (priority, selections)
        self._update()

    def clear(self, text_format=None):
        """Remove the highlighting for the given QTextCharFormat.

        If ``text_format`` is None, removes all highlighting.

        """
        if text_format:
            key = id(text_format)
            try:
                del self._formats[key]
            except KeyError:
                pass
            try:
                del self._selections[key]
            except KeyError:
                return
        else:
            self._formats.clear()
            self._selections.clear()
        self._update()

    def _update(self):
        """(Internal) Called whenever the arbitrary highlighting changes."""
        textedit = self.parent()
        if textedit:
            selections = sorted(self._selections.values(), key=operator.itemgetter(0))
            ess = sum(map(operator.itemgetter(1), selections), [])
            textedit.setExtraSelections(ess)

    def delete(self):
        """Reimplemented to remove all highlighting before delete."""
        self.clear()
        super().delete()

