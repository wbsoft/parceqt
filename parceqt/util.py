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

