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

from PyQt5.QtCore import QThread


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


class SingleInstance:
    """Keeps a single instance around for another object.

    We keep only a weak reference to the object, if the object is garbage
    collected, we disappear as well.

    """
    @classmethod
    def instance(cls, obj, *args, **kwargs):
        """Get or create the instance for obj."""
        try:
            return cls._instances[obj]
        except AttributeError:
            cls._instances = weakref.WeakKeyDictionary()
        except KeyError:
            pass
        # target must be in place before init is called
        new = cls._instances[obj] = cls.__new__(cls)
        new._target = weakref.ref(obj)
        new.__init__(obj, *args, **kwargs)
        return new

    @classmethod
    def delete_instance(cls, obj):
        """Actively remove the stored instance."""
        try:
            instance = cls._instances[obj]
        except (KeyError, AttributeError):
            pass
        else:
            instance.delete()

    @classmethod
    def get_instance(cls, obj):
        """Return the instance if it already exists, else returns None."""
        try:
            return cls._instances[obj]
        except (AttributeError, KeyError):
            pass

    def target_object(self):
        """Return the object we are stored for."""
        return self._target()

    def delete(self):
        """Delete the stored reference to ourself.

        Other cleanup code could be added by reimplementing this method.
        This is not called on garbage collection, but only when called
        directly or via delete_instance().

        """
        obj = self._target()
        if obj is not None:
            del self.__class__._instances[obj]


class Switch:
    """A context manager that evaluates to True when in a context, else to False.

    Example::

        clicking = Switch()

        def myfunc():
            with clicking:
                blablabl()

        # and elsewhere:
        def blablabl():
            if not clicking:
                do_something()

        # when blablabl() is called from myfunc, clicking evaluates to True,
        # so do_something() is not called then.

    """
    def __init__(self):
        self._value = 0

    def __enter__(self):
        self._value += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._value -= 1

    def __bool__(self):
        return bool(self._value)


def call_async(function, finished=None):
    """Call ``function()`` in a background thread and then ``finished()`` when
    done in the main thread."""
    return Job(function, finished)


def call_async_with_result(function, finished=None):
    """Call ``result = function()`` in a background thread and then
    ``finished(result)`` when done in the main thread."""
    return Job(function, finished, True)


