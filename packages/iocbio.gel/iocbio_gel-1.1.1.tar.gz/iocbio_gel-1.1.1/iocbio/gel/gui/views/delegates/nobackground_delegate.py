#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, QObject
from PySide6.QtGui import QBrush


class NoBackgroundDelegate(QStyledItemDelegate):
    """
    This delegate drops background set by model's BackgroundRole. In this case, it
    avoids showing selected gel image using (usually grey) background around image.
    Note that list view navigation feedback (such as background change showing current
    image) works as it is set separately.
    """

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.brush = QBrush()

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        option.backgroundBrush = self.brush
