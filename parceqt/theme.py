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
Use parce.theme.Theme with QTextCharFormat.
"""


from PyQt5.QtGui import QColor, QFont, QTextCharFormat

import parce.theme


class Theme(parce.theme.Theme):
    """Theme, inheriting from parce.Theme, but using Qt text formats by default."""
    def __init__(self, filename, factory=None):
        """Reimplemented to use the text_format factory by default."""
        super().__init__(filename, factory or text_format)


class MetaTheme(Theme, parce.theme.MetaTheme):
    """MetaTheme that uses Qt text formats by default."""


def _color(c):
    """Convert css.Color to QColor."""
    return QColor(c.r, c.g, c.b, c.a * 255)


def _font_point_size(size, unit):
    """Return a suitable point size, where 12 is a default value."""
    if isinstance(size, str):
        return {
            "xx-small": 8,
            "x-small": 9,
            "small": 10,
            "medium": 12,
            "large": 14,
            "x-large": 16,
            "xx-large": 20,
            "xxx-large": 24,
            "larger": 14,
            "smaller": 10,
        }.get(size, 12)
    elif unit == "pt":
        return size
    elif unit == "px":
        return size * 12 / 16
    elif unit in ("rem", "em"):
        return size * 12
    elif unit == "%":
        return size * 12 / 100
    return 12


def _font_stretch(stretch):
    """Return a suitable font stretch."""
    if isinstance(stretch, str):
        return {
            "ultra-condensed": 50,
            "extra-condensed": 62,
            "condensed": 75,
            "semi-condensed": 87,
            "normal": 100,
            "semi-expanded": 112,
            "expanded": 125,
            "extra-expanded": 150,
            "ultra-expanded": 200,
        }.get(stretch, 100)
    return int(stretch)


def _font_weight(weight):
    """Return a suitable weight."""
    if isinstance(weight, str):
        if weight == "bold":
            return QFont.Bold
        elif weight == "bolder":
            return QFont.ExtraBold
        elif weight == "lighter":
            return QFont.Light
    else:
        if weight >= 900:
            return QFont.Black
        elif weight >= 800:
            return QFont.ExtraBold
        elif weight >= 700:
            return QFont.Bold
        elif weight >= 600:
            return QFont.DemiBold
        elif weight >= 500:
            return QFont.Medium
        elif weight >= 400:
            return QFont.Normal
        elif weight >= 300:
            return QFont.Light
        elif weight >= 200:
            return QFont.ExtraLight
        else:
            return QFont.Thin
    return QFont.Normal


def text_format(properties):
    """A Factory to be used with parce.theme.Theme.

    Creates a QTextCharFormat for the css properties.

    """
    f = QTextCharFormat()
    p = parce.theme.TextFormat(properties)
    if p.color:
        f.setForeground(_color(p.color))
    if p.background_color:
        f.setBackground(_color(p.background_color))
    if p.text_decoration_line:
        if 'underline' in p.text_decoration_line:
            f.setFontUnderline(True)
        if 'overline' in p.text_decoration_line:
            f.setFontOverline(True)
        if 'line-through' in p.text_decoration_line:
            f.setFontStrikeOut(True)
    if p.text_decoration_style:
        s = p.text_decoration_style
        if s == "solid":
            f.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        #elif s == "double":
        #    pass # Seems Qt5 does not provide this
        elif s == "dotted":
            f.setUnderlineStyle(QTextCharFormat.DotLine)
        elif s == "dashed":
            f.setUnderlineStyle(QTextCharFormat.DashUnderline)
        elif s == "wavy":
            f.setUnderlineStyle(QTextCharFormat.WaveUnderline)
    if p.text_decoration_color:
        f.setUnderlineColor(_color(p.text_decoration_color))
    if p.font_family:
        f.setFontFamilies(p.font_family)
    if p.font_size:
        f.setFontPointSize(_font_size(p.font_size, p.font_size_unit))
    if p.font_stretch:
        f.setFontStretch(_font_stretch(p.font_stretch))
    if p.font_style in ('italic', 'oblique'):
        f.setFontItalic(True)
    if p.font_variant_caps == "small-caps":
        f.setFontCapitalization(QFont.SmallCaps)
    if p.font_weight:
        f.setFontWeight(_font_weight(p.font_weight))
    if not f.isEmpty():
        return f

