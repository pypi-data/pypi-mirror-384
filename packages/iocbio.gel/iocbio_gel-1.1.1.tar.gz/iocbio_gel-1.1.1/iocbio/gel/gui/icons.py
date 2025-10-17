#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap

from iocbio.gel.gui import style
from iocbio.gel.gui.resources import rc_icons  # noqa: F401


class SvgIcon(QIcon):
    def __init__(self, image, color: str = None) -> None:
        super().__init__(image)
        self.color = color

    def pixmap(self, *args, **kwargs) -> QPixmap:
        return self._with_color(super().pixmap(*args, **kwargs))

    def _with_color(self, pixmap: QPixmap) -> QPixmap:
        if self.color is None:
            return pixmap

        qp = QPainter(pixmap)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect(pixmap.rect(), QColor(self.color))
        qp.end()

        return pixmap


ADD_IMAGE = SvgIcon(":/icons/feather/image.svg", style.ICON_COLOR)
LOADING_IMAGE = SvgIcon(":/icons/feather/coffee.svg", style.ICON_COLOR)
MISSING_IMAGE = SvgIcon(":/icons/feather/x.svg", "#D02F30")
FOLDER = SvgIcon(":/icons/feather/folder.svg", style.ICON_COLOR)
SELECT_ROW = SvgIcon(":/icons/feather/arrow-right.svg", style.ICON_COLOR)
ADD_ROW = SvgIcon(":/icons/feather/plus.svg", style.ICON_COLOR)
