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
LanguageMenuAction is a QAction that shows a section-based submenu for
all languages in the/a parce :class:`~parce.registry.Registry`.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu

import parce.registry



class LanguageMenuAction(QAction):
    """A QAction that shows a section-based submenu for all languages in the/a
    parce :class:`~parce.registry.Registry`.

    """
    lexicon_changed = pyqtSignal(object)
    """This signal is emitted when a language is selected by the user.

    The single argument is a :class:`~parce.lexicon.Lexicon` or None.

    """

    def __init__(self, parent=None, registry=None):
        super().__init__(parent)
        self._registry = None
        self._actionGroup = QActionGroup(self, triggered=self._slot_language_selected)
        self.setMenu(QMenu("", None))
        self.set_registry(registry or parce.registry.registry)

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

        By default the desc and the name between parentheses from the
        registry's entry is returned. If the qualname is None or the empty
        string, returns ``"None"``.

        """
        if qualname:
            entry = self.registry()[qualname]
            return "{0.desc} ({0.name})".format(entry)
        return "None"

    def set_lexicon(self, lexicon):
        """Set the current lexicon, or None."""
        for a in self._actionGroup.findChildren(QAction):
            if ((lexicon and a.objectName() == lexicon.qualname) or
                (not lexicon and not a.objectName())):
                a.setChecked(True)
                return
        a = self._actionGroup.checkedAction()
        if a:
            a.setChecked(False)

    def lexicon(self):
        """Return the current lexicon."""
        a = self._actionGroup.checkedAction()
        if a:
            qualname = a.objectName()
            if qualname:
                r = self.registry()
                return r.lexicon(qualname)

    def _slot_language_selected(self, action):
        """Called when an action is triggered."""
        qualname = action.objectName()
        lexicon = self.registry().lexicon(qualname) if qualname else None
        self.lexicon_changed.emit(lexicon)

    def _populate(self):
        """Called to fill ourselves with submenus from the registry."""
        g = self._actionGroup
        m = self.menu()
        for a in g.findChildren(QAction):
            a.setParent(None)
            a.deleteLater()
        actions = m.actions()
        insert_before = None
        if not actions:
            # menu is empty
            a = QAction(g, text="&None", objectName="", checkable=True, checked=True)
            m.addAction(a)
            m.addSeparator()
        else:
            # make it empty
            for index, a in enumerate(actions):
                if a.objectName() == "sect_submenu":
                    insert_before = a
                    break
            else:
                if len(actions) > 2:
                    insert_before = actions[2]
        reg = self.registry().by_section()
        for sect in sorted(reg):
            if sect:
                submenu = QMenu()
                a = QAction(sect, m, objectName="sect_submenu")
                a.setMenu(submenu)
                m.insertAction(insert_before, a) if insert_before else m.addAction(a)
                entries = sorted((self.display_name(qualname), qualname) for qualname in reg[sect].keys())
                for name, qualname in entries:
                    submenu.addAction(QAction(g, text=name, objectName=qualname, checkable=True))
        # old items left?
        if actions and index:
            for a in actions[index:]:
                if a.objectName() == "sect_submenu":
                    a.setParent(None)
                    a.deleteLater()

