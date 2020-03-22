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
from PyQt5.QtWidgets import (
    QHBoxLayout, QMainWindow, QPlainTextEdit, QPushButton, QSplitter, QTreeView,
    QVBoxLayout, QWidget,
)

import parce
import parceqt.treemodel


class DebugWindow(QMainWindow):
    """A main window to edit text and examine the generated token structure.

    Example::

        from PyQt5.Qt import *
        a=QApplication([])

        from parceqt.debug import DebugWindow
        w = DebugWindow()
        w.resize(1200,900)
        w.show()

        w.set_theme("default")
        w.adjust_widget()

        from parce.lang.css import *
        w.set_root_lexicon(Css.root)
        w.set_text(open("path/to/parce/themes/default.css").read())

    In the debug window you can edit the text at the left and directly at the
    right examine the tree structure. Along the top of the window the path to
    the token at the current cursor position is displayed, from the root
    lexicon upto the token, from which the action is displayed.

    Clicking a button selects the associated range of the context or token in
    the text view. Clicking an item in the tree also selects that range in the
    text.

    Moving the cursor in the text updates the current item in the tree,
    and the displayed ancestor path.

    """
    def __init__(self, parent=None):
        super().__init__(parent)
        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QVBoxLayout(margin=4, spacing=2)
        widget.setLayout(layout)

        self.ancestorView = AncestorView(self)
        layout.addWidget(self.ancestorView, 0)

        splitter = QSplitter(self, orientation=Qt.Horizontal)
        layout.addWidget(splitter, 100)

        self.textEdit = QPlainTextEdit()
        self.treeView = QTreeView()

        splitter.addWidget(self.textEdit)
        splitter.addWidget(self.treeView)

        self.document = d = self.textEdit.document()
        self.textEdit.setDocument(self.document)

        self.builder = b = parceqt.builder(d)
        m = parceqt.treemodel.TreeModel.from_builder(b)
        self.treeView.setModel(m)

        # signal connections
        self.ancestorView.node_clicked.connect(self.slot_node_clicked)
        b.updated.connect(self.slot_cursor_position_changed)
        self.textEdit.cursorPositionChanged.connect(self.slot_cursor_position_changed)
        self.treeView.clicked.connect(self.slot_item_clicked)

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
            self.ancestorView.set_token_path(token)
            index = self.treeView.model().get_model_index(token)
            self.treeView.setCurrentIndex(index)
        elif tree is not None:
            self.ancestorView.clear()

    def slot_item_clicked(self, index):
        tree = self.builder.get_root()
        if tree:
            node = self.treeView.model().get_node(index)
            cursor = self.textEdit.textCursor()
            cursor.setPosition(node.end)
            cursor.setPosition(node.pos, QTextCursor.KeepAnchor)
            self.textEdit.setTextCursor(cursor)
            self.textEdit.setFocus()

    def slot_node_clicked(self, node):
        tree = self.builder.get_root()
        if tree and node.root() is tree:
            cursor = self.textEdit.textCursor()
            cursor.setPosition(node.end)
            cursor.setPosition(node.pos, QTextCursor.KeepAnchor)
            self.textEdit.setTextCursor(cursor)
            self.textEdit.setFocus()
            index = self.treeView.model().get_model_index(node)
            self.treeView.expand(index)
            self.treeView.setCurrentIndex(index)


class AncestorView(QWidget):
    """Displays a horizontal row of buttons for a token."""
    node_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clicking = False
        layout = QHBoxLayout(margin=0, spacing=0)
        self.setLayout(layout)
        self.root_button = QPushButton(self)
        layout.addWidget(self.root_button)
        self.clear()

    def clear(self):
        self.root_button.setText("...")
        item = self.layout().takeAt(1)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = self.layout().takeAt(1)

    def set_token_path(self, token):
        if self._clicking:
            return # don't redraw if the cursor moved because of us
        self.clear()
        layout = self.layout()
        nodes = [token]
        nodes.extend(token.ancestors())
        nodes.reverse()
        def buttons():
            yield nodes[0], self.root_button
            for n in nodes[1:]:
                button = QPushButton(self)
                def activate(node=n):
                    self._clicking = True
                    self.node_clicked.emit(node)
                    self._clicking = False
                button.pressed.connect(activate)
                yield n, button
        curlang = None
        for n, button in buttons():
            if n.is_context:
                name = n.lexicon.name()
                lang, lexicon = name.split('.')
                text = lexicon if lang == curlang else name
                curlang = lang
            else:
                text = repr(n.action)
            button.setText(text)
            layout.addWidget(button)
        layout.addStretch(10)

