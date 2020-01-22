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

from parce.treebuilder import BackgroundTreeBuilder

from . import util


class Job(QThread):
    def __init__(self, builder):
        super().__init__()
        self.builder = builder

    def run(self):
        self.builder.process_changes()


class TreeBuilder(util.SingleInstance, QObject, BackgroundTreeBuilder):
    """A BackgroundTreeBuilder that uses Qt signals instead of callbacks.

    This TreeBuilder is attachted to a QTextDocument, and automatically
    updates the tokens when the document changes.

    """
    updated = pyqtSignal(int, int)  # emitted when one full run finished
    changed = pyqtSignal(int, int)  # emitted when a contents change falls in one block

    def __init__(self, document, root_lexicon=None):
        QObject.__init__(self, document)
        BackgroundTreeBuilder.__init__(self, root_lexicon)
        document.contentsChange.connect(self.slot_contents_change)
        text = document.toPlainText()
        if text:
            with self.change() as c:
                c.change_contents(text)

    def document(self):
        """Return the QTextDocument, which is our parent."""
        return self.parent()

    def start_processing(self):
        """Start a background job if needed."""
        if not self.job:
            j = self.job = Job(self)
            j.finished.connect(self.finish_processing)
            j.start()

    def build_updated(self):
        """Reimplemented to emit the updated() signal."""
        super().build_updated()
        self.updated.emit(self.start, self.end)

    def wait(self):
        """Wait for completion if a background job is running."""
        job = self.job
        if job and job.isRunning():
            # we can't simply job.wait() because signals that are executed
            # in the main thread would then deadlock.
            loop = QEventLoop()
            job.finished.connect(loop.quit)
            loop.exec_()

    def root_lexicon(self):
        """Return the currently (being) set root lexicon."""
        c = self.changes
        if c and c.root_lexicon != False:
            return c.root_lexicon
        return self.root.lexicon

    def set_root_lexicon(self, root_lexicon):
        """Set the root lexicon to use to tokenize the text. Triggers a rebuild."""
        if root_lexicon != self.root_lexicon():
            with self.change() as c:
                c.change_root_lexicon(self.document().toPlainText(), root_lexicon)

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
        with self.change() as c:
            c.change_contents(doc.toPlainText(), start, removed, added)


