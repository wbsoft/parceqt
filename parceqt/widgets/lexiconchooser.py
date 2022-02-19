# -*- coding: utf-8 -*-
#
# This file is part of the parce-qt Python package.
#
# Copyright © 2022 by Wilbert Berendsen <info@wilbertberendsen.nl>
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
LexiconChooser is a combobox to choose a root lexicon.
"""


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox

import parce.registry


class LexiconChooser(QComboBox):
    """A combobox showing available root lexicons.

    On instantiation the :class:`~parce.registry.Registry` can be given. If
    None, the default parce registry is used.

    """

    lexicon_changed = pyqtSignal(object)
    """This signal is emitted when the current lexicon changes.

    The single argument is a :class:`~parce.lexicon.Lexicon` or None.

    """

    def __init__(self, parent=None, registry=None):
        self._registry = None
        super().__init__(parent)
        self.set_registry(registry or parce.registry.registry)
        self.currentIndexChanged.connect(self._slot_current_index_changed)

    def set_registry(self, registry):
        """Set the :class:`~parce.registry.Registry` and populate ourselves
        with the lexicons from the registry.

        """
        self._registry = registry
        self._populate()

    def registry(self):
        """Return the currently set Registry."""
        return self._registry

    def display_name(self, qualname):
        """Return the text to display for the ``qualname``.

        By default the name from the registry's entry is returned.
        If the qualname is None or the empty string, returns ``"None"``.

        """
        if qualname:
            return self.registry()[qualname].name
        return "None"

    def _populate(self):
        """Populate the combobox with the available root lexicons in the registry."""
        self.clear()
        items = [(self.display_name(None), None)]
        items.extend(sorted((self.display_name(qualname), qualname) for qualname in self.registry().keys()))
        self._items, self._qualnames = zip(*items)
        self.addItems(self._items)

    def _lexicon(self, index):
        """Return a lexicon or None for the item at ``index``."""
        qualname = self._qualnames[index]
        if qualname:
            return self.registry().lexicon(qualname)

    def set_lexicon(self, lexicon):
        """Set the current lexicon (a :class:`~parce.lexicon.Lexicon` or None)."""
        name = lexicon.qualname if lexicon else None
        try:
            i = self._qualnames.index(name)
        except ValueError:
            pass
        else:
            self.setCurrentIndex(i)

    def lexicon(self):
        """Return the current lexicon."""
        return self._lexicon(self.currentIndex())

    def _slot_current_index_changed(self, i):
        """Called on index change, emits the lexicon_changed signal."""
        self.lexicon_changed.emit(self._lexicon(i))


