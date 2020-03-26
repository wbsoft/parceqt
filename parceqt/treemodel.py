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

"""


from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


class TreeModel(QAbstractItemModel):
    """TreeModel implements QAbstractItemModel to show a parce tree in
    Qt widgets such as a QTreeView.

    """
    CONTEXT_FLAGS = Qt.ItemIsSelectable | Qt.ItemIsEnabled
    TOKEN_FLAGS = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren

    def __init__(self, tree, parent=None):
        super().__init__(parent)
        self._reset_in_progress = False
        self._root = tree

    @classmethod
    def from_builder(cls, builder):
        """Instantiate a TreeModel that keeps itselves updated whenever
        the specified parceqt TreeBuilder updates.

        """
        model = cls(builder.root)
        builder.started.connect(model.slot_build_started)
        builder.updated.connect(model.slot_build_finished)
        return model

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
        if role == Qt.DisplayRole and index.isValid():
            node = index.internalPointer()
            return repr(node)

    def flags(self, index):
        if index.isValid() and index.internalPointer().is_token:
            return self.TOKEN_FLAGS
        return self.CONTEXT_FLAGS

    def headerData(self, column, orientation, role):
        """Reimplemented to not show the root element's repr while busy."""
        if column == 0 and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return repr(self._root) if not self._reset_in_progress else "..." # busy indicator

    ## own methods
    def get_model_index(self, node):
        """Return a QModelIndex for the specified node (Context or Token)."""
        return self.createIndex(node.parent_index(), 0, node)

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


