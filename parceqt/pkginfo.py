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
Meta-information about the parce-qt package.

This information is used by the install script, and can be queried
from other applications.

"""

import collections
Version = collections.namedtuple("Version", "major minor patch")



#: name of the package
name = "parceqt"

#: the current version
version = Version(0, 17, 0)
version_suffix = ""
version_string = "{}.{}.{}".format(*version) + version_suffix

#: short description
description = "The parceqt Python module"

#: long description
long_description = \
    "Small module providing parce parsing and highlighting for Qt"

#: maintainer name
maintainer = "Wilbert Berendsen"

#: maintainer email
maintainer_email = "info@wilbertberendsen.nl"

#: homepage
url = "https://github.com/wbsoft/parceqt"

#: license
license = "GPL"

#: copyright year
copyright_year = "2020"

