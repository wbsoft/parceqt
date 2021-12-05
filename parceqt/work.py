# -*- coding: utf-8 -*-
#
# This file is part of the parce-qt Python package.
#
# Copyright © 2021 by Wilbert Berendsen <info@wilbertberendsen.nl>
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
The Worker class, inheriting from parce's Worker class.
"""


from PyQt5.QtCore import pyqtSignal, QEventLoop, QObject

import parce.work

from . import util


class Worker(util.SingleInstance, parce.work.Worker, QObject):
    """A Worker that uses Qt signals instead of callbacks.

    This Worker is attachted to a QTextDocument, and automatically updates the
    tokens (and optionally the transformed result) when the document changes.

    """
    tree_updated = pyqtSignal(int, int)
    tree_finished = pyqtSignal()
    transform_finished = pyqtSignal()

    debugging = True    #TMP

    def __init__(self, qtextdocument, treebuilder=None, transformer=None):
        if treebuilder is None:
            from .treebuilder import TreeBuilder
            treebuilder = TreeBuilder(qtextdocument)
        QObject.__init__(self, qtextdocument)
        parce.work.Worker.__init__(self, treebuilder, transformer)
        qtextdocument.contentsChange.connect(self.slot_contents_change)
        text = qtextdocument.toPlainText()
        if text:
            self.update(text)

    ## added methods
    def document(self):
        """Return the QTextDocument, which is our parent."""
        return self.parent()

    def slot_contents_change(self, start, removed, added):
        """Called after modification of the text, retokenizes the modified part."""
        self.update(self.document().toPlainText(), False, start, removed, added)

    ## reimplemented methods
    def run_process(self):
        """Reimplemented to run parts of the process in a Qt Thread."""
        process = self.process()

        def fg():
            for stage in process:
                if self.debugging:
                    print("Processing stage FG:", stage)
                if stage in ("tree_build", "transform_build"):
                    return util.call_async(bg, fg)

        def bg():
            for stage in process:
                if self.debugging:
                    print("Processing stage BG:", stage)
                break

        fg()

    def wait_build(self):
        """Wait for the build job to be completed.

        Immediately returns if there is no build job active.

        """
        with self._condition:
            if self._tree_state & parce.work.REPLACE == 0:
                return
        loop = QEventLoop()
        self.tree_finished.connect(loop.quit)
        loop.exec_()

    def wait_transform(self):
        """Wait for the transform job to be completed.

        Immediately returns if there is no transform job active.

        """
        with self._condition:
            if self._transform_state & parce.work.REPLACE == 0:
                return
        loop = QEventLoop()
        self.transform_finished.connect(loop.quit)
        loop.exec_()

    def finish_build(self):
        """Reimplemented to emit the ``tree_updated`` and
        ``tree_finished``signals.

        """
        self.tree_updated.emit(self.builder().start, self.builder().end)
        self.tree_finished.emit()
        return super().finish_build()

    def finish_transform(self):
        """Reimplemented to emit the ``transform_finished`` signal.

        """
        self.transform_finished.emit()
        return super().finish_transform()

