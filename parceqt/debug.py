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
This module provides a debug window to show/edit text and the tokenized tree.
"""

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QTextCursor, QTextDocument
from PyQt5.QtWidgets import QMainWindow, QPlainTextEdit, QSplitter, QTreeView

import parce
import parceqt.treemodel


class DebugWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        splitter = QSplitter(self, orientation=Qt.Horizontal)
        self.setCentralWidget(splitter)

        self.textEdit = QPlainTextEdit()
        self.treeView = QTreeView()

        splitter.addWidget(self.textEdit)
        splitter.addWidget(self.treeView)

        self.document = d = self.textEdit.document()
        self.textEdit.setDocument(self.document)

        self.builder = b = parceqt.builder(d)
        m = parceqt.treemodel.TreeModel.from_builder(b)
        self.treeView.setModel(m)

        b.updated.connect(self.slot_cursor_position_changed)
        self.textEdit.cursorPositionChanged.connect(self.slot_cursor_position_changed)

    def set_text(self, text):
        """Set the text in the text edit."""
        self.document.setPlainText(text)

    def set_root_lexicon(self, lexicon):
        """Set the root lexicon to use."""
        parceqt.set_root_lexicon(self.document, lexicon)

    def set_theme(self, theme="default"):
        """Set the theme to use for the text edit."""
        parceqt.highlight(self.document, theme)

    def adjust_widget(self):
        """Adjust the text edit's palette to the theme."""
        parceqt.adjust_widget(self.textEdit)

    def slot_cursor_position_changed(self):
        """Called when the text cursor moved."""
        tree = self.builder.get_root()
        if tree:
            pos = self.textEdit.textCursor().position()
            token = tree.find_token(pos)
            index = self.treeView.model().get_model_index(token)
            self.treeView.setCurrentIndex(index)

