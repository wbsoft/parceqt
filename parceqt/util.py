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
Various utility classes and functions.
"""

import weakref

from PyQt5.QtCore import QObject, QThread


_jobs = set()   # store running Job instances


class Job(QThread):
    """Simple QThread helper that runs a ``function`` in a background thread.

    If you specify a ``finished`` callable, it will be called when the function
    has finished. If ``with_result`` is True, the ``finished`` callable will
    be called with the result of the function.

    The job is started immediately. You do not need to store the job, it will
    keep a reference itself as long as it is running.

    """
    def __init__(self, function, finished=None, with_result=False):
        super().__init__()
        self._function = function
        self._finished = finished
        self._with_result = with_result
        _jobs.add(self)
        self.finished.connect(self._slot_finished)
        self.start()

    def run(self):
        """Run the function and store the result."""
        self._result = self._function()

    def _slot_finished(self):
        _jobs.discard(self)
        if self._finished is not None:
            if self._with_result:
                self._finished(self._result)
            else:
                self._finished()


class SingleInstance(QObject):
    """Keeps a single instance around for another object.

    We keep only a weak reference to the object, if the object is garbage
    collected, we disappear as well.

    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)

    @classmethod
    def instance(cls, parent, *args, **kwargs):
        """Get or create the instance for ``parent``."""
        instance = parent.findChild(cls)
        if not instance:
            instance = cls(parent, *args, **kwargs)
        return instance

    @classmethod
    def delete_instance(cls, parent):
        """Actively remove the stored instance."""
        instance = parent.findChild(cls)
        if instance:
            instance.delete()

    @classmethod
    def get_instance(cls, parent):
        """Return the instance if it already exists, else returns None."""
        return parent.findChild(cls)

    def delete(self):
        """Delete the stored reference to ourself.

        Other cleanup code could be added by reimplementing this method.
        This is not called on garbage collection, but only when called
        directly or via delete_instance().

        """
        self.setParent(None)
        self.deleteLater()


def call_async(function, finished=None):
    """Call ``function()`` in a background thread and then ``finished()`` when
    done in the main thread."""
    return Job(function, finished)


def call_async_with_result(function, finished=None):
    """Call ``result = function()`` in a background thread and then
    ``finished(result)`` when done in the main thread."""
    return Job(function, finished, True)


