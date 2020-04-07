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
    QApplication, QComboBox, QHBoxLayout, QMainWindow, QPlainTextEdit,
    QPushButton, QSplitter, QStatusBar, QTextEdit, QTreeView, QVBoxLayout,
    QWidget,
)

import parce.language
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

    show_updated_region_enabled = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clear_timer = QTimer(timeout=self.clear_updated_region, singleShot=True)

        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QVBoxLayout(margin=4, spacing=2)
        widget.setLayout(layout)

        top_layout = QHBoxLayout(margin=0, spacing=0)

        self.lexiconChooser = LexiconChooser(self)
        self.ancestorView = AncestorView(self)
        top_layout.addWidget(self.lexiconChooser)
        top_layout.addWidget(self.ancestorView)
        top_layout.addStretch(10)
        layout.addLayout(top_layout)

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
        self.setStatusBar(QStatusBar())
        self.create_model()

        # signal connections
        self.lexiconChooser.lexicon_changed.connect(self.slot_root_lexicon_changed)
        self.ancestorView.node_clicked.connect(self.slot_node_clicked)
        b.started.connect(self.slot_build_started)
        b.updated.connect(self.slot_build_updated)
        self.textEdit.cursorPositionChanged.connect(self.slot_cursor_position_changed)
        self.treeView.clicked.connect(self.slot_item_clicked)

        self.textEdit.setFocus()

    def create_model(self):
        """Instantiate a tree model for the tree view."""
        m = parceqt.treemodel.TreeModel(self.builder.root)
        m.connect_debugging_builder(self.builder)
        self.treeView.setModel(m)

    def delete_model(self):
        """Delete the model and remove it from the tree."""
        m = self.treeView.model()
        if m:
            m.disconnect_debugging_builder(self.builder)
            self.treeView.setModel(None)
            m.deleteLater()

    def set_text(self, text):
        """Set the text in the text edit."""
        self.document.setPlainText(text)

    def set_root_lexicon(self, lexicon):
        """Set the root lexicon to use."""
        self.lexiconChooser.set_root_lexicon(lexicon)

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
        tree = self.builder.get_root()
        self.lexiconChooser.setToolTip(parceqt.treemodel.TreeModel.node_tooltip(tree))
        if self.show_updated_region_enabled:
            self.show_updated_region()

    def slot_cursor_position_changed(self):
        """Called when the text cursor moved."""
        tree = self.builder.get_root()
        if tree:
            pos = self.textEdit.textCursor().position()
            token = tree.find_token(pos)
            self.ancestorView.set_token_path(token)
            model = self.treeView.model()
            if model:
                index = model.get_model_index(token)
                self.treeView.setCurrentIndex(index)
        elif tree is not None:
            self.ancestorView.clear()

    def slot_item_clicked(self, index):
        tree = self.builder.get_root()
        if tree:
            model = self.treeView.model()
            if model:
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
            model = self.treeView.model()
            if model:
                index = model.get_model_index(node)
                self.treeView.expand(index)
                self.treeView.setCurrentIndex(index)

    def slot_root_lexicon_changed(self, lexicon):
        self.builder.set_root_lexicon(lexicon)

    def show_updated_region(self):
        end = self.builder.end
        if end >= self.document.characterCount() - 1:
            end = self.document.characterCount() - 1
            if self.builder.start == 0:
                return
        c = QTextCursor(self.document)
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
        self.setLayout(QHBoxLayout(margin=0, spacing=0))
        self.clear()

    def clear(self):
        layout = self.layout()
        item = layout.takeAt(0)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = layout.takeAt(0)

    def set_token_path(self, token):
        if self._clicking:
            return # don't redraw if the cursor moved because of us
        self.clear()
        layout = self.layout()

        nodes = [token]
        nodes.extend(token.ancestors())
        del nodes[-1]   # leave out the root context
        nodes.reverse()
        names = list(lexicon_names(n.lexicon for n in nodes[:-1]))
        names.append(repr(token.action))
        tooltips = map(parceqt.treemodel.TreeModel.node_tooltip, nodes)
        for node, name, tip in zip(nodes, names, tooltips):
            button = QPushButton(self)
            button.setMinimumWidth(8)
            def activate(node=node):
                with self._clicking:
                    self.node_clicked.emit(node)
            button.pressed.connect(activate)
            button.setText(name)
            button.setToolTip(tip)
            layout.addWidget(button)


class LexiconChooser(QComboBox):
    """A combobox showing available lexicons."""
    lexicon_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.populate()
        self.currentIndexChanged.connect(self.slot_current_index_changed)

    def populate(self):
        """Populate the combobox with the available root lexicons in parce."""
        self.clear()
        self.lexicons = list(root_lexicons())
        self.addItems([l.name() for l in self.lexicons])

    def set_root_lexicon(self, lexicon):
        """Set the current root lexicon, may also be a new one, which is appended then."""
        try:
            i = self.lexicons.index(lexicon)
        except ValueError:
            i = len(self.lexicons)
            self.lexicons.append(lexicon)
            self.addItem(lexicon.name())
        self.setCurrentIndex(i)

    def root_lexicon(self):
        """Return the current root lexicon."""
        return self.lexicons[self.currentIndex()]

    def slot_current_index_changed(self, i):
        """Called on index change, emits the lexicon_changed signal."""
        self.lexicon_changed.emit(self.lexicons[i])


class TreeBuilder(parceqt.treebuilder.TreeBuilder):
    """Inherited from to add some debugging capabilities."""
    begin_remove_rows = pyqtSignal(object, int, int)
    end_remove_rows = pyqtSignal()
    begin_insert_rows = pyqtSignal(object, int, int)
    end_insert_rows = pyqtSignal()
    change_position = pyqtSignal(object, int, int)
    change_root_lexicon = pyqtSignal()

    def process(self):
        for stage in super().process():
            print("Processing stage:", stage)
            yield stage

    def process_finished(self):
        """Reimplemented to emit the ``updated`` signal."""
        super().process_finished()

    def replace_nodes(self, context, slice_, nodes):
        """Reimplemented for fine-grained signals."""
        start, end = get_slice(context, slice_)
        end -= 1
        if start < len(context) and start <= end:
            self.begin_remove_rows.emit(context, start, end)
            del context[slice_]
            self.end_remove_rows.emit()
        if nodes:
            self.begin_insert_rows.emit(context, start, start + len(nodes) - 1)
            context[start:start] = nodes
            self.end_insert_rows.emit()

    def replace_pos(self, context, slice_, offset):
        """Reimplemented for fine-grained signals."""
        super().replace_pos(context, slice_, offset)
        start, end = get_slice(context, slice_)
        end -= 1
        if start < len(context) and start <= end:
            self.change_position.emit(context, start, end)

    def replace_root_lexicon(self, lexicon):
        """Reimplemented for fine-grained signals."""
        super().replace_root_lexicon(lexicon)
        self.change_root_lexicon.emit()


def root_lexicons():
    """Get the root lexicons of all languages bundled with parce."""
    for lang in parce.language.get_all_languages():
        root = getattr(lang, "root", None)
        if root:
            yield root


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


def get_slice(context, slice_):
    """Return a tuple(start, end) for the ``slice_`` of the ``context``.

    None is interpreted corrrectly and incorrect values are corrected.
    End is in fact 1 after the last, just as for Python slices.

    """
    total = len(context)
    start = slice_.start
    if start is None or start < -total:
        start = 0
    elif start < 0:
        start += total
    end = slice_.stop
    if end is None or end > total:
        end = total
    elif end < -total:
        end = 0
    elif end < 0:
        end += total
    return start, end
