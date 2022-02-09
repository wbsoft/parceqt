# -*- coding: utf-8 -*-
#
# This file is part of the parce-qt Python package.
#
# Copyright © 2020-2021 by Wilbert Berendsen <info@wilbertberendsen.nl>
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
This module implements a TreeBuilder emitting Qt signals.
"""

from PyQt5.QtCore import pyqtSignal, QObject

import parce.treebuilder

from . import util


class TreeBuilder(parce.treebuilder.TreeBuilder, QObject):
    """A TreeBuilder that uses Qt signals instead of callbacks.

    The signals ``begin_*``, ``end_*``, ``change_*`` signals can be used to
    connect a QAbstractItemModel to a tree builder, they are not needed for
    normal operation.

    """
    started = pyqtSignal()              #: emitted when a new update job started
    updated = pyqtSignal(int, int)      #: emitted when one full run finished
    preview = pyqtSignal(int, object)   #: emitted with premature tree when peek_threshold is reached

    #: emitted before removing a slice of nodes (Context, first, last)
    begin_remove_rows = pyqtSignal(object, int, int)

    #: emitted after removing nodes
    end_remove_rows = pyqtSignal()

    #: emitted before inserting nodes (Context, first, last)
    begin_insert_rows = pyqtSignal(object, int, int)

    #: emitted after inserting nodes
    end_insert_rows = pyqtSignal()

    #: emitted when a slice of Tokens changes position (Context, first, last)
    change_position = pyqtSignal(object, int, int)

    #: emitted when the root lexicon has changed
    change_root_lexicon = pyqtSignal()

    #: after how many characters a build preview is presented
    peek_threshold = 5000

    def __init__(self, document):
        QObject.__init__(self, document)
        parce.treebuilder.TreeBuilder.__init__(self)

    def peek(self, start, tree):
        """Reimplemented to get a sneak preview."""
        self.preview.emit(start, tree)
        super().peek(start, tree)

    def replace_nodes(self, context, slice_, nodes):
        """Reimplemented for fine-grained signals."""
        start, end, _step = slice_.indices(len(context))
        end -= 1
        if start < len(context) and start <= end:
            self.begin_remove_rows.emit(context, start, end)
            del context[slice_]
            self.end_remove_rows.emit()
        if nodes:
            self.begin_insert_rows.emit(context, start, start + len(nodes) - 1)
            context[start:start] = nodes
            self.end_insert_rows.emit()

    def replace_pos(self, context, index, offset):
        """Reimplemented for fine-grained signals."""
        super().replace_pos(context, index, offset)
        start, end = index, len(context) - 1
        if start <= end:
            self.change_position.emit(context, start, end)

    def replace_root_lexicon(self, lexicon):
        """Reimplemented for fine-grained signals."""
        super().replace_root_lexicon(lexicon)
        self.change_root_lexicon.emit()

    def process_started(self):
        """Reimplemented to emit the started signal."""
        self.started.emit()
        super().process_started()

    def process_finished(self):
        """Reimplemented to emit the updated signal."""
        self.updated.emit(self.start, self.end)
        super().process_finished()

