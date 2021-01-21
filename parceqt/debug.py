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

Use::

    $ python3 -m parceqt.debug  <filename>

You can also create a debug window in an interactive session; see the class
documentation.

The debug window shows highlighted text, and the tokenized tree structure.

"""


import operator
import weakref

from PyQt5.QtCore import pyqtSignal, QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import (
    QColor, QFont, QKeySequence, QPalette, QTextCharFormat, QTextCursor,
    QTextDocument,
)
from PyQt5.QtWidgets import (
    QAction, QActionGroup, QApplication, QComboBox, QFileDialog, QHBoxLayout,
    QMainWindow, QMenu, QMenuBar, QPlainTextEdit, QPushButton, QSplitter,
    QStatusBar, QTextEdit, QTreeView, QVBoxLayout, QWidget,
)

import parce.formatter
import parce.language
import parce.theme
import parce.themes
import parce.util
import parceqt
import parceqt.highlighter
import parceqt.treebuilder
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

    show_updated_region_enabled = False

    def __init__(self, parent=None):
        super().__init__(parent, windowTitle="parceqt debugger")

        f = self._updated_format = QTextCharFormat()
        c = QColor("palegreen")
        c.setAlpha(64)
        f.setBackground(c)
        f = self._currentline_format = QTextCharFormat()
        f.setProperty(QTextCharFormat.FullWidthSelection, True)

        self._actions = Actions(self)
        self._actions.add_menus(self.menuBar())

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

        self.textEdit = QPlainTextEdit(lineWrapMode=QPlainTextEdit.NoWrap, cursorWidth=2)
        self.treeView = QTreeView()

        splitter.addWidget(self.textEdit)
        splitter.addWidget(self.treeView)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.extraSelectionManager = ExtraSelectionManager(self.textEdit)

        self.document = d = self.textEdit.document()
        self.textEdit.setDocument(self.document)

        self.builder = b = parceqt.TreeBuilder.instance(d)
        b.debugging = True

        self.setStatusBar(QStatusBar())
        self.create_model()

        # signal connections
        self.textEdit.viewport().installEventFilter(self)
        self.textEdit.installEventFilter(self)
        self.lexiconChooser.lexicon_changed.connect(self.slot_root_lexicon_changed)
        self.ancestorView.node_clicked.connect(self.slot_node_clicked)
        b.started.connect(self.slot_build_started)
        b.updated.connect(self.slot_build_updated)
        self.textEdit.cursorPositionChanged.connect(self.slot_cursor_position_changed)
        self.treeView.clicked.connect(self.slot_item_clicked)

        self.textEdit.setFocus()
        self.set_theme()

        # somewhat larger font by default
        font = self.textEdit.font()
        font.setPointSizeF(11)
        self.textEdit.setFont(font)

    def create_model(self):
        """Instantiate a tree model for the tree view."""
        m = self.treeView.model()
        if not m:
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

    def open_file(self, filename):
        """Read a file from disk and guess the language."""
        text = read_file(filename)
        root_lexicon = parce.find(filename=filename, contents=text)
        self.set_text(text)
        self.set_root_lexicon(root_lexicon)
        c = self.textEdit.textCursor()
        c.setPosition(0)
        self.textEdit.setTextCursor(c)

    def set_theme(self, theme="default", adjust_widget=True):
        """Set the theme to use for the text edit."""
        if isinstance(theme, str):
            theme = parce.theme_by_name(theme)
        formatter = parceqt.formatter.Formatter(theme) if theme else None
        if adjust_widget:
            if formatter:
                font = formatter.font(self)
                self.textEdit.setPalette(formatter.palette(self))
            else:
                font = QApplication.font(self)
                self.textEdit.setPalette(QApplication.palette(self))
            font.setPointSizeF(self.textEdit.font().pointSizeF()) # keep size
            self.textEdit.setFont(font)
            self.highlight_current_line()
        h = parceqt.highlighter.SyntaxHighlighter.instance(self.builder)
        h.set_formatter(formatter)

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
            doc = parceqt.document.Document(self.document, self.builder)
            token = doc.token(pos)
            if token:
                self.ancestorView.set_token_path(token)
                model = self.treeView.model()
                if model:
                    index = model.get_model_index(token)
                    self.treeView.setCurrentIndex(index)
        elif tree is not None:
            self.ancestorView.clear()
        self.highlight_current_line()

    def slot_item_clicked(self, index):
        """Called when a node in the tree view is clicked."""
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
        """Called when a button in the ancestor view is clicked."""
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
        """Called when the root lexicon is changed."""
        self.builder.set_root_lexicon(lexicon)

    def highlight_current_line(self):
        """Highlight the current line."""
        group = QPalette.Active if self.textEdit.hasFocus() else QPalette.Inactive
        p = self.textEdit.palette()
        color = p.color(group, QPalette.AlternateBase)
        self._currentline_format.setBackground(color)
        if color != p.color(group, QPalette.Base):
            c = self.textEdit.textCursor()
            c.clearSelection()
            self.extraSelectionManager.highlight(self._currentline_format, [c])
        else:
            self.extraSelectionManager.clear(self._currentline_format)

    def show_updated_region(self):
        """Highlight the updated region for 2 seconds."""
        end = self.builder.end
        if end >= self.document.characterCount() - 1:
            end = self.document.characterCount() - 1
            if self.builder.start == 0:
                return
        c = QTextCursor(self.document)
        c.setPosition(end)
        c.setPosition(self.builder.start, QTextCursor.KeepAnchor)
        self.extraSelectionManager.highlight(self._updated_format, [c], msec=2000)

    def clear_updated_region(self):
        self.extraSelectionManager.clear(self._updated_format)

    def eventFilter(self, obj, ev):
        """Implemented to support Ctrl+wheel zooming and keybfocus handling."""
        if obj == self.textEdit:
            if ev.type() in (QEvent.FocusIn, QEvent.FocusOut):
                self.highlight_current_line()
        else:   # viewport
            if ev.type() == QEvent.Wheel and ev.modifiers() == Qt.ControlModifier:
                if ev.angleDelta().y() > 0:
                    self.textEdit.zoomIn()
                elif ev.angleDelta().y() < 0:
                    self.textEdit.zoomOut()
                return True
        return False


class AncestorView(QWidget):
    """Displays a horizontal row of buttons for a token."""
    node_clicked = pyqtSignal(object)

    _clicking = parce.util.Switch()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout(margin=0, spacing=0))
        self.clear()

    def clear(self):
        """Delete all buttons."""
        layout = self.layout()
        item = layout.takeAt(0)
        while item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            item = layout.takeAt(0)

    def set_token_path(self, token):
        """Create buttons for the token and its ancestors."""
        if self._clicking:
            return # don't redraw if the cursor moved because of us
        self.clear()
        layout = self.layout()

        nodes = [token]
        nodes.extend(token.ancestors())
        nodes.reverse()
        names = list(lexicon_names(n.lexicon for n in nodes[:-1]))
        names.append(repr(token.action))
        del nodes[0], names[0]
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
        self.lexicons = [None]
        self.lexicons.extend(root_lexicons())
        self.addItems(map(repr, self.lexicons))

    def set_root_lexicon(self, lexicon):
        """Set the current root lexicon, may also be a new one, which is appended then."""
        try:
            i = self.lexicons.index(lexicon)
        except ValueError:
            i = len(self.lexicons)
            self.lexicons.append(lexicon)
            self.addItem(repr(lexicon))
        self.setCurrentIndex(i)

    def root_lexicon(self):
        """Return the current root lexicon."""
        return self.lexicons[self.currentIndex()]

    def slot_current_index_changed(self, i):
        """Called on index change, emits the lexicon_changed signal."""
        self.lexicon_changed.emit(self.lexicons[i])


class Actions:
    """Container for all the QActions and their implementations."""
    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.create_actions()
        self.set_action_defaults()
        self.connect_actions()
        self.set_action_texts()
        self.set_action_shortcuts()

    def create_actions(self):
        self.file_open = QAction()
        self.edit_copy_html = QAction()
        self.view_tree = QAction(checkable=True)
        self.view_tree_expand = QAction()
        self.view_tree_collapse = QAction()
        self.view_updated_region = QAction(checkable=True)
        self.view_theme = QAction()
        self.view_theme_reload = QAction()
        m = QMenu()
        self.view_theme.setMenu(m)
        g = self.view_theme_actiongroup = QActionGroup(None)
        a = QAction(g, checkable=True)
        a.setText("&None")
        a.setObjectName("None")
        m.addAction(a)
        m.addSeparator()
        for name in parce.themes.get_all_themes():
            a = QAction(g, checkable=True)
            a.setText(name)
            m.addAction(a)
        m.addSeparator()
        m.addAction(self.view_theme_reload)

    def set_action_texts(self):
        self.file_open.setText("&Open File...")
        self.edit_copy_html.setText("&Copy selection as HTML")
        self.view_tree.setText("Show &Tree Structure")
        self.view_tree_expand.setText("&Expand All")
        self.view_tree_collapse.setText("&Collapse All")
        self.view_updated_region.setText("Show &Updated Region")
        self.view_theme.setText("T&heme")
        self.view_theme_reload.setText("&Reload Theme")

    def set_action_shortcuts(self):
        self.file_open.setShortcut(QKeySequence("Ctrl+O"))
        self.view_tree.setShortcut(QKeySequence("Ctrl+T"))
        self.view_theme_reload.setShortcut(QKeySequence("F5"))

    def set_action_defaults(self):
        self.view_tree.setChecked(True)
        self.view_updated_region.setChecked(False)
        for a in self.view_theme_actiongroup.actions():
            if a.text() == "default":
                a.setChecked(True)
                break

    def add_menus(self, menubar):
        """Populate a menu bar."""
        filemenu = QMenu("&File", menubar)
        filemenu.addAction(self.file_open)
        editmenu = QMenu("&Edit", menubar)
        editmenu.addAction(self.edit_copy_html)
        viewmenu = QMenu("&View", menubar)
        viewmenu.addAction(self.view_theme)
        viewmenu.addSeparator()
        viewmenu.addAction(self.view_tree)
        viewmenu.addAction(self.view_tree_expand)
        viewmenu.addAction(self.view_tree_collapse)
        viewmenu.addSeparator()
        viewmenu.addAction(self.view_updated_region)
        menubar.addMenu(filemenu)
        menubar.addMenu(editmenu)
        menubar.addMenu(viewmenu)

    def connect_actions(self):
        self.file_open.triggered.connect(self.open_file)
        self.edit_copy_html.triggered.connect(self.copy_html)
        self.view_tree.triggered.connect(self.toggle_tree_visibility)
        self.view_tree_expand.triggered.connect(self.tree_expand_all)
        self.view_tree_collapse.triggered.connect(self.tree_collapse_all)
        self.view_updated_region.triggered.connect(self.toggle_updated_region_visibility)
        self.view_theme_actiongroup.triggered.connect(self.slot_view_theme_selected)
        self.view_theme_reload.triggered.connect(self.reload_theme)

    def open_file(self):
        """Implementation of Open File action."""
        filename, filetype = QFileDialog.getOpenFileName(self.mainwindow, "Open File")
        if filename:
            self.mainwindow.open_file(filename)

    def copy_html(self):
        """Copy selected text as HTML."""
        c = parceqt.cursor(self.mainwindow.textEdit.textCursor())
        c.copy_html()

    def toggle_tree_visibility(self, checked):
        """Handle Show Tree Structure checkbox toggle."""
        self.mainwindow.create_model() if checked else self.mainwindow.delete_model()
        self.mainwindow.treeView.setVisible(checked)

    def toggle_updated_region_visibility(self, checked):
        """Handle Show Updated Region checkbox toggle."""
        self.mainwindow.show_updated_region_enabled = checked

    def slot_view_theme_selected(self, action):
        """Switch to the selected theme."""
        if action.objectName() == "None":
            theme = None
        else:
            theme = action.text()
        self.mainwindow.set_theme(theme)

    def tree_expand_all(self):
        """Implementation of Expand All action."""
        self.mainwindow.treeView.expandAll()

    def tree_collapse_all(self):
        """Implementation of Collapse All action."""
        self.mainwindow.treeView.collapseAll()

    def reload_theme(self):
        """Reload the theme."""
        action = self.view_theme_actiongroup.checkedAction()
        if action:
            self.slot_view_theme_selected(action)


class ExtraSelectionManager(QObject):
    """Manages highlighting of arbitrary sections in a Q(Plain)TextEdit.

    Stores and highlights lists of QTextCursors on a per-format basis.

    """
    def __init__(self, edit):
        """Initializes ourselves with a Q(Plain)TextEdit as parent."""
        QObject.__init__(self, edit)
        self._selections = {}
        self._formats = {} # store the QTextFormats

    def highlight(self, text_format, cursors, priority=0, msec=0):
        """Highlights the selection of an arbitrary list of QTextCursors.

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
        self.update()

    def clear(self, text_format):
        """Removes the highlighting for the given QTextCharFormat."""
        key = id(text_format)
        try:
            del self._formats[key]
        except KeyError:
            pass
        try:
            del self._selections[key]
        except KeyError:
            pass
        else:
            self.update()

    def update(self):
        """(Internal) Called whenever the arbitrary highlighting changes."""
        textedit = self.parent()
        if textedit:
            selections = sorted(self._selections.values(), key=operator.itemgetter(0))
            ess = sum(map(operator.itemgetter(1), selections), [])
            textedit.setExtraSelections(ess)


def root_lexicons():
    """Get the root lexicons of all languages bundled with parce."""
    lexicons = []
    for lang in parce.language.get_all_languages():
        root = getattr(lang, "root", None)
        if root:
            lexicons.append(root)
    lexicons.sort(key=repr)
    return lexicons


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


def read_file(filename):
    """Read the contents of a file, if the encoding fails, read in latin1."""
    try:
        return open(filename).read()
    except UnicodeError:
        return open(filename, encoding="latin1").read()


if __name__ == '__main__':
    a = QApplication([])
    w = DebugWindow()
    w.resize(900, 550)
    w.show()
    import sys
    if len(sys.argv) > 1:
        w.open_file(sys.argv[1])
    sys.exit(a.exec_())

