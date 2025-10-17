#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QPainter


class SelectableRowDelegate(QStyledItemDelegate):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._row = -1
        parent.signals.highlighted_row_changed.connect(self.on_highlighted_row_changed)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if index.isValid() and self._row == index.row():
            option.state |= QStyle.State_Selected
        super().paint(painter, option, index)

    def on_highlighted_row_changed(self, row: int):
        self._row = row
