#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from datetime import datetime

from PySide6.QtWidgets import QWidget, QStyleOptionViewItem, QDateTimeEdit
from PySide6.QtCore import Qt, QLocale, QModelIndex, QDateTime, QAbstractItemModel

from iocbio.gel.gui.views.delegates.selectable_row_delegate import SelectableRowDelegate


class DateTimeDelegate(SelectableRowDelegate):
    def displayText(self, value, locale: QLocale) -> str:
        return locale.toString(value, QLocale.ShortFormat)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        widget = QDateTimeEdit(parent)
        widget.setMaximumDateTime(QDateTime.currentDateTime())
        widget.setCalendarPopup(True)
        return widget

    def setEditorData(self, editor: QDateTimeEdit, index: QModelIndex) -> None:
        data = index.model().data(index, Qt.EditRole)
        editor.setDateTime(data)

    def setModelData(
        self, editor: QDateTimeEdit, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        date_time = editor.dateTime()
        date = date_time.date()
        time = date_time.time()
        model.setData(
            index,
            datetime(date.year(), date.month(), date.day(), time.hour(), time.minute()),
            Qt.EditRole,
        )
