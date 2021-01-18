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
This module implements a BackgroundTreeBuilder encapsulating a QTextDocument.

Because it knows the document, it has access to the text, and therefore
we implement root_lexicon() and set_root_lexicon() here.

The TreeBuilder emits the updated(start, end) signal whenever new tokens
are generated.

"""

from PyQt5.QtCore import pyqtSignal, QEventLoop, QObject
from PyQt5.QtGui import QTextBlock

import parce.treebuilder

from . import util


class TreeBuilder(util.SingleInstance, parce.treebuilder.TreeBuilder, QObject):
    """A TreeBuilder that uses Qt signals instead of callbacks.

    This TreeBuilder is attachted to a QTextDocument, and automatically
    updates the tokens when the document changes.

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
    peek_threshold = 2000

    #: set to True to print some debugging info to the console.
    debugging = False

    def __init__(self, document, root_lexicon=None):
        QObject.__init__(self, document)
        parce.treebuilder.TreeBuilder.__init__(self, root_lexicon)
        document.contentsChange.connect(self.slot_contents_change)
        text = document.toPlainText()
        if text:
            self.rebuild(text)

    def document(self):
        """Return the QTextDocument, which is our parent."""
        return self.parent()

    def process(self):
        """Reimplemented to print some debugging info if desired."""
        for stage in super().process():
            if self.debugging:
                print("Processing stage:", stage)
            yield stage

    def start_processing(self):
        """Reimplemented to start a background job."""
        self._process = self.process()
        self.process_loop()

    def process_loop(self):
        """Run the process; call a background thread for the "update" stage."""
        for stage in self._process:
            if stage == "build":
                return util.call_async(self.background_loop, self.process_loop)
        if not self.busy:
            # during process_finished() a new process might have started
            del self._process

    def background_loop(self):
        """Run the background (build) part of the process."""
        for stage in self._process:
            break

    def process_started(self):
        """Reimplemented to emit the ``started`` signal."""
        self.started.emit()
        super().process_started()

    def process_finished(self):
        """Reimplemented to emit the ``updated`` signal."""
        self.updated.emit(self.start, self.end)
        super().process_finished()

    def wait(self):
        """Wait for completion if a background job is running."""
        if self.busy:
            # we can't simply job.wait() because signals that are executed
            # in the main thread would then deadlock.
            loop = QEventLoop()
            self.updated.connect(loop.quit)
            loop.exec_()

    def peek(self, start, tree):
        """Reimplemented to get a sneak preview."""
        self.preview.emit(start, tree)
        super().peek(start, tree)

    def root_lexicon(self):
        """Return the current root lexicon."""
        return self.root.lexicon

    def set_root_lexicon(self, root_lexicon):
        """Set the root lexicon to use to tokenize the text. Triggers a rebuild."""
        self.rebuild(self.document().toPlainText(), root_lexicon)

    def slot_contents_change(self, start, removed, added):
        """Called after modification of the text, retokenizes the modified part."""
        self.rebuild(self.document().toPlainText(), False, start, removed, added)

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

