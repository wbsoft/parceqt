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
A Formatter that uses parce.theme.Theme with QTextCharFormat.
"""


from PyQt5.QtGui import QColor, QFont, QPalette, QTextCharFormat
from PyQt5.QtWidgets import QApplication

import parce.formatter


class Formatter(parce.formatter.Formatter):
    """Formatter, inheriting from parce.Formatter, but using Qt text formats by default."""
    def __init__(self, theme, factory=None):
        """Reimplemented to use the text_format factory by default."""
        super().__init__(theme, factory or text_format)

    def font(self, widget=None):
        """Return the font of the default text format.

        This font can then be used for a text editing widget. If widget is
        specified, resolves the application's default font for the widget with
        the properties from the theme.

        """
        font = QApplication.font(widget)
        f = self.baseformat()
        if f:
            font = f.font().resolve(font)
        return font

    def palette(self, widget=None):
        """Return a QPalette with the following colors set:

            ``QPalette.Text``
                default foreground color
            ``QPalette.Base``
                default background color
            ``QPalette.HighlightText``
                selection foreground color
            ``QPalette.Highlight``
                selection background color
            ``QPalette.AlternateBase``
                background color for the current line

        If the theme supports it, the Inactive and Disabled color groups are
        set to their own colors. Otherwise, they just use the same colors.

        If widget is specified, resolves the application's default palette for
        the widget with the properties from the theme.

        """
        # all color groups
        p = QApplication.palette(widget)
        f = self.baseformat("window")  # QTextCharFormat
        if f:
            p.setColor(QPalette.Text, f.foreground().color())
            p.setColor(QPalette.Base, f.background().color())
        f = self.baseformat("selection")
        if f:
            p.setColor(QPalette.HighlightedText, f.foreground().color())
            p.setColor(QPalette.Highlight, f.background().color())
        f = self.baseformat("current-line")
        if f:
            p.setColor(QPalette.AlternateBase, f.background().color())

        # Active color group
        f = self.baseformat("window", "focus")
        if f:
            p.setColor(QPalette.Active, QPalette.Text, f.foreground().color())
            p.setColor(QPalette.Active, QPalette.Base, f.background().color())
        f = self.baseformat("selection", "focus")
        if f:
            p.setColor(QPalette.Active, QPalette.HighlightedText, f.foreground().color())
            p.setColor(QPalette.Active, QPalette.Highlight, f.background().color())
        f = self.baseformat("current-line", "focus")
        if f:
            p.setColor(QPalette.Active, QPalette.AlternateBase, f.background().color())

        # Disabled color group
        f = self.baseformat("window", "disabled")
        if f:
            p.setColor(QPalette.Disabled, QPalette.Text, f.foreground().color())
            p.setColor(QPalette.Disabled, QPalette.Base, f.background().color())
        f = self.baseformat("selection", "disabled")
        if f:
            p.setColor(QPalette.Disabled, QPalette.HighlightedText, f.foreground().color())
            p.setColor(QPalette.Disabled, QPalette.Highlight, f.background().color())
        f = self.baseformat("current-line", "disabled")
        if f:
            p.setColor(QPalette.Disabled, QPalette.AlternateBase, f.background().color())
        return p


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


def text_format(tf):
    """A factory to be used with parce.theme.Formatter.

    Creates a QTextCharFormat for the specified TextFormat object.

    """
    if tf:
        f = QTextCharFormat()
        if tf.color:
            f.setForeground(_color(tf.color))
        if tf.background_color:
            f.setBackground(_color(tf.background_color))
        if tf.text_decoration_line:
            if 'underline' in tf.text_decoration_line:
                f.setFontUnderline(True)
            if 'overline' in tf.text_decoration_line:
                f.setFontOverline(True)
            if 'line-through' in tf.text_decoration_line:
                f.setFontStrikeOut(True)
        if tf.text_decoration_style:
            s = tf.text_decoration_style
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
        if tf.text_decoration_color:
            f.setUnderlineColor(_color(tf.text_decoration_color))
        if tf.font_family:
            try:
                f.setFontFamilies(tf.font_family)
            except AttributeError: # this property was introduced in Qt 5.13
                f.setFontFamily(tf.font_family[0])
        if tf.font_size:
            f.setFontPointSize(_font_point_size(tf.font_size, tf.font_size_unit))
        if tf.font_stretch:
            f.setFontStretch(_font_stretch(tf.font_stretch))
        if tf.font_style in ('italic', 'oblique'):
            f.setFontItalic(True)
        if tf.font_variant_caps == "small-caps":
            f.setFontCapitalization(QFont.SmallCaps)
        if tf.font_weight:
            f.setFontWeight(_font_weight(tf.font_weight))
        if not f.isEmpty():
            return f

