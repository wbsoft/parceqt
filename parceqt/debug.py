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

from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor, QTextDocument
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QPlainTextEdit, QPushButton,
    QSplitter, QStatusBar, QTextEdit, QTreeView, QVBoxLayout, QWidget,
)

import parce
import parceqt
import parceqt.highlighter
import parceqt.treebuilder
import parceqt.treemodel
import parceqt.util


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
        self._clear_timer = QTimer(timeout=self.clear_updated_region, singleShot=True)

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
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.document = d = self.textEdit.document()
        self.textEdit.setDocument(self.document)

        self.builder = b = TreeBuilder.instance(d)
        m = parceqt.treemodel.TreeModel.from_builder(b)
        self.treeView.setModel(m)

        self.setStatusBar(QStatusBar())

        # signal connections
        self.ancestorView.node_clicked.connect(self.slot_node_clicked)
        b.started.connect(self.slot_build_started)
        b.updated.connect(self.slot_build_updated)
        self.textEdit.cursorPositionChanged.connect(self.slot_cursor_position_changed)
        self.treeView.clicked.connect(self.slot_item_clicked)

        self.textEdit.setFocus()

    def set_text(self, text):
        """Set the text in the text edit."""
        self.document.setPlainText(text)

    def set_root_lexicon(self, lexicon):
        """Set the root lexicon to use."""
        self.builder.set_root_lexicon(lexicon)

    def set_theme(self, theme="default", adjust_widget=True):
        """Set the theme to use for the text edit."""
        h = parceqt.highlighter.SyntaxHighlighter.instance(self.builder)
        if isinstance(theme, str):
             theme = parce.theme_by_name(theme)
        h.set_theme(theme)
        if adjust_widget:
            if theme:
                f = parceqt.formatter.Formatter(theme)
                font = f.font()
                if font:
                    self.textEdit.setFont(font)
                self.textEdit.setPalette(f.palette())
            else:
                self.textEdit.setFont(QApplication.font(w))
                self.textEdit.setPalette(QApplication.palette(w))

    def adjust_widget(self):
        """Adjust the text edit's palette to the theme."""
        parceqt.adjust_widget(self.textEdit)

    def slot_build_started(self):
        """Called when the tree builder has started a build."""
        self.treeView.setCursor(Qt.BusyCursor)

    def slot_build_updated(self):
        """Called when the tree builder has finished a build."""
        self.treeView.unsetCursor()
        self.slot_cursor_position_changed()
        self.statusBar().showMessage(", ".join(lexicon_names(self.builder.lexicons)))
        self.show_updated_region()

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

    def show_updated_region(self):
        c = QTextCursor(self.document)
        end = self.builder.end
        if end >= self.document.characterCount():
            end -= 1
        c.setPosition(end)
        c.setPosition(self.builder.start, QTextCursor.KeepAnchor)
        f = QTextCharFormat()
        f.setBackground(QColor("palegreen"))
        es = QTextEdit.ExtraSelection()
        es.cursor = c
        es.format = f
        self.textEdit.setExtraSelections([es])
        self._clear_timer.start(2000)

    def clear_updated_region(self):
        self.textEdit.setExtraSelections([])


class AncestorView(QWidget):
    """Displays a horizontal row of buttons for a token."""
    node_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clicking = parceqt.util.Switch()
        layout = QHBoxLayout(margin=0, spacing=0)
        self.setLayout(layout)
        self.root_button = QPushButton(self)
        layout.addWidget(self.root_button)
        self.clear()

    def clear(self):
        self.root_button.setText("...")
        layout = self.layout()
        item = layout.takeAt(1)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = layout.takeAt(1)
        layout.addStretch(10)

    def set_token_path(self, token):
        if self._clicking:
            return # don't redraw if the cursor moved because of us
        self.clear()
        layout = self.layout()
        layout.takeAt(1)
        nodes = [token]
        nodes.extend(token.ancestors())
        nodes.reverse()
        names = list(lexicon_names(n.lexicon for n in nodes[:-1]))
        names.append(repr(token.action))
        tooltip = parceqt.treemodel.TreeModel.node_tooltip
        tooltips = list(tooltip(n) for n in nodes[1:])
        self.root_button.setText(names[0])
        self.root_button.setToolTip(tooltip(nodes[0]))
        for node, name, tip in zip(nodes[1:], names[1:], tooltips):
            button = QPushButton(self)
            button.setMinimumWidth(8)
            def activate(node=node):
                with self._clicking:
                    self.node_clicked.emit(node)
            button.pressed.connect(activate)
            button.setText(name)
            button.setToolTip(tip)
            layout.addWidget(button)
        layout.addStretch(10)


class TreeBuilder(parceqt.treebuilder.TreeBuilder):
    """Inherited from to add some debugging capabilities."""
    def process(self):
        for stage in super().process():
            print("Processing stage: ", stage)
            yield stage

    def process_finished(self):
        """Reimplemented to emit the ``updated`` signal."""
        print(f"Updated: {self.start}-{self.end}")
        super().process_finished()


def lexicon_names(lexicons):
    """Yield the names of the lexicons with the language removed if
    that is the same as the previous lexicon's language.

    """
    curlang = None
    for l in lexicons:
        fullname = repr(l)
        lang, name = fullname.split('.')
        if lang == curlang:
            yield name
        else:
            yield fullname
            curlang = lang


