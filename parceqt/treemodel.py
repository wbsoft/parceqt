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
This module implements TreeModel, which inherits from QAbstractItemModel
and provides a model for a tree structure.

This can be used for debugging the tree using a Qt gui.
See also the debug module.

"""


import reprlib

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


class TreeModel(QAbstractItemModel):
    """TreeModel implements QAbstractItemModel to show a parce tree in
    Qt widgets such as a QTreeView.

    """
    CONTEXT_FLAGS = Qt.ItemIsSelectable | Qt.ItemIsEnabled
    TOKEN_FLAGS = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren

    CONTEXT_FORMAT = "{name} at {pos} ({count})"
    TOKEN_FORMAT = "{action} {text} at {pos} {group}"

    CONTEXT_TOOLTIP = (
        "Context: {name}\n"
        "Pos: {pos} - {end} (length: {length})\n"
        "Child count: {count}\n"
        "Parent: {parent}\n"
        "Parent-index: {index}")

    TOKEN_TOOLTIP = (
        "Token: {text}\n"
        "Pos: {pos} - {end} (length: {length})\n"
        "Action: {action}\n"
        "Group: {group}\n"
        "Parent: {parent}\n"
        "Parent-index: {index}")

    def __init__(self, tree, parent=None):
        super().__init__(parent)
        self._reset_in_progress = False
        self._root = tree

    def connect_builder(self, builder):
        """Connect to the started and finished signals of a TreeBuilder."""
        builder.started.connect(self.slot_build_started)
        builder.updated.connect(self.slot_build_finished)

    def disconnect_builder(self, builder):
        """Disconnect from the started and finished signals of a TreeBuilder."""
        builder.started.disconnect(self.slot_build_started)
        builder.updated.disconnect(self.slot_build_finished)

    def connect_debugging_builder(self, builder):
        """Connect to all the signals of a debugging tree builder.

        (See the :mod:`debug` module).

        """
        builder.begin_remove_rows.connect(self.slot_begin_remove_rows)
        builder.end_remove_rows.connect(self.slot_end_remove_rows)
        builder.begin_insert_rows.connect(self.slot_begin_insert_rows)
        builder.end_insert_rows.connect(self.slot_end_insert_rows)
        builder.change_position.connect(self.slot_change_position)
        builder.change_root_lexicon.connect(self.slot_change_root_lexicon)

    def disconnect_debugging_builder(self, builder):
        """Disconnect from all the signals of a debugging tree builder.

        (See the :mod:`debug` module).

        """
        builder.begin_remove_rows.disconnect(self.slot_begin_remove_rows)
        builder.end_remove_rows.disconnect(self.slot_end_remove_rows)
        builder.begin_insert_rows.disconnect(self.slot_begin_insert_rows)
        builder.end_insert_rows.disconnect(self.slot_end_insert_rows)
        builder.change_position.disconnect(self.slot_change_position)
        builder.change_root_lexicon.disconnect(self.slot_change_root_lexicon)

    ## reimplemented virtual methods
    def index(self, row, column, parent):
        if self.hasIndex(row, column, parent):
            node = parent.internalPointer() if parent.isValid() else self._root
            if 0 <= row < len(node):
                return self.createIndex(row, column, node[row])
        return QModelIndex()

    def parent(self, index):
        if index.isValid():
            parent = index.internalPointer().parent
            if parent and not parent.is_root():
                return self.createIndex(parent.parent_index(), 0, parent)
        return QModelIndex()

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        if parent.column() <= 0:
            node = parent.internalPointer() if parent.isValid() else self._root
            if node.is_context:
                return len(node)
        return 0

    def data(self, index, role):
        if index.isValid():
            node = index.internalPointer()
            if role == Qt.DisplayRole:
                return self.node_repr(node)
            elif role == Qt.ToolTipRole:
                return self.node_tooltip(node)

    def flags(self, index):
        if index.isValid() and index.internalPointer().is_token:
            return self.TOKEN_FLAGS
        return self.CONTEXT_FLAGS

    def headerData(self, column, orientation, role):
        """Reimplemented to not show the root element's repr while busy."""
        if not self._reset_in_progress and column == 0 and orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.node_repr(self._root)
            elif role == Qt.ToolTipRole:
                return self.node_tooltip(self._root)

    ## own methods
    def root(self):
        """Return the tree's root element."""
        return self._root

    def get_model_index(self, node):
        """Return a QModelIndex for the specified node (Context or Token)."""
        if node.parent:
            return self.createIndex(node.parent_index(), 0, node)
        return QModelIndex()

    def get_node(self, index):
        """Return the node (Context or Token) for the specified QModelIndex."""
        return index.internalPointer() if index.isValid() else self._root

    def slot_build_started(self):
        """Called when tree builder starts."""
        self._reset_in_progress = True
        self.beginResetModel()

    def slot_build_finished(self):
        """Called when tree builder has finished."""
        self._reset_in_progress = False
        self.endResetModel()

    def slot_begin_remove_rows(self, node, first, last):
        self.beginRemoveRows(self.get_model_index(node), first, last)

    def slot_end_remove_rows(self):
        self.endRemoveRows()

    def slot_begin_insert_rows(self, node, first, last):
        self.beginInsertRows(self.get_model_index(node), first, last)

    def slot_end_insert_rows(self):
        self.endInsertRows()

    def slot_change_position(self, node, first, last):
        index = self.get_model_index(node)
        self.dataChanged.emit(index, index)
        # the following would be locigal but is very slow:
        #topleft = self.get_model_index(node[first])
        #bottomright = self.get_model_index(node[last])
        #self.dataChanged.emit(topleft, bottomright)

    def slot_change_root_lexicon(self):
        self.headerDataChanged.emit(Qt.Horizontal, 0, 0)

    @staticmethod
    def node_dict(node):
        """Return a dictionary with information about the node."""
        d = dict(
            pos = node.pos,
            end = node.end,
            length = node.end - node.pos,
        )
        if node.is_token:
            d.update(
                text = reprlib.repr(node.text),
                action = node.action,
                group = "" if node.group is None else format(node.group)
            )
        else:
            d.update(
                name = node.lexicon,
                count = "1 child" if len(node) == 1 else f"{len(node)} children"
            )
        return d

    @classmethod
    def node_tooltip(cls, node):
        """Return text for a tooltip for the node."""
        d = cls.node_dict(node)
        d.update(
            index = node.parent_index() if node.parent else "-",
            parent = cls.node_repr(node.parent) if node.parent else "-",
        )
        if node.is_token:
            if not d['group']:
                d['group'] = "-"
        template = cls.TOKEN_TOOLTIP if node.is_token else cls.CONTEXT_TOOLTIP
        return template.format(**d).strip()

    @classmethod
    def node_repr(cls, node):
        """Return short text to decribe the node for a tree view."""
        d = cls.node_dict(node)
        template = cls.TOKEN_FORMAT if node.is_token else cls.CONTEXT_FORMAT
        if node.is_token:
            if d['group']:
                d['group'] = "({})".format(d['group'])
        return template.format(**d).strip()


