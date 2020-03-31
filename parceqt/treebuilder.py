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

from PyQt5.QtCore import pyqtSignal,QEventLoop, QObject, QThread
from PyQt5.QtGui import QTextBlock

import parce.treebuilder

from . import util


class Job(QThread):
    def __init__(self, builder):
        super().__init__()
        self.builder = builder

    def run(self):
        self.builder.process_changes()


class TreeBuilder(util.SingleInstance, QObject, parce.treebuilder.TreeBuilder):
    """A TreeBuilder that uses Qt signals instead of callbacks.

    This TreeBuilder is attachted to a QTextDocument, and automatically
    updates the tokens when the document changes.

    """
    started = pyqtSignal()          #: emitted when a new update job started
    updated = pyqtSignal(int, int)  #: emitted when one full run finished
    changed = pyqtSignal(int, int)  #: emitted when a contents change falls in one block

    def __init__(self, document, root_lexicon=None):
        QObject.__init__(self, document)
        parce.treebuilder.TreeBuilder.__init__(self, root_lexicon)
        self.job = None
        document.contentsChange.connect(self.slot_contents_change)
        text = document.toPlainText()
        if text:
            self.change_text(text)

    def document(self):
        """Return the QTextDocument, which is our parent."""
        return self.parent()

    def do_processing(self):
        """Start a background job if needed."""
        j = self.job = Job(self)
        j.finished.connect(self.finish_processing)
        j.start()

    def process_started(self):
        """Reimplemented to emit the ``started`` signal."""
        self.started.emit()

    def process_finished(self):
        """Reimplemented to clear the job attribute and emit the ``updated`` signal."""
        self.job = None
        self.updated.emit(self.start, self.end)

    def wait(self):
        """Wait for completion if a background job is running."""
        if self.busy:
            # we can't simply job.wait() because signals that are executed
            # in the main thread would then deadlock.
            loop = QEventLoop()
            self.updated.connect(loop.quit)
            loop.exec_()

    def get_root(self, wait=False):
        """Get the root element of the completed tree.

        If wait is True, this call blocks until tokenizing is done, and the
        full tree is returned. If wait is False, None is returned if the tree
        is still busy being built.

        Note that, for the lifetime of a TreeBuilder, the root element is always
        the same. The root element is also accessible in the `root` attribute.
        But using this method you can be sure that you are dealing with a
        complete and fully intact tree.

        """
        if self.busy:
            if not wait:
                return
            self.wait()
        return self.root

    def root_lexicon(self):
        """Return the current root lexicon."""
        return self.root.lexicon

    def set_root_lexicon(self, root_lexicon):
        """Set the root lexicon to use to tokenize the text. Triggers a rebuild."""
        self.change_root_lexicon(self.document().toPlainText(), root_lexicon)

    def slot_contents_change(self, start, removed, added):
        """Called after modification of the text, retokenizes the modified part."""
        # if the change is in one block, emit a special signal immediately
        doc = self.document()
        b = doc.findBlock(start)
        leftover = b.position() + b.length() - start
        if leftover > 2:
            if added < leftover and removed < leftover:
                if added != removed:
                    # formats need to be shifted in the current block
                    self.changed.emit(start, added - removed)
            else:
                # formats need to be cleared from start
                self.changed.emit(start, 0)
        self.change_text(doc.toPlainText(), start, removed, added)


