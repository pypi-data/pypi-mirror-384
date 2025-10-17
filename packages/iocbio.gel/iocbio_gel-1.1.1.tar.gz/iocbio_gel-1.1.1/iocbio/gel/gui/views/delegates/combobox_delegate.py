#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QWidget, QStyleOptionViewItem, QComboBox
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel

from iocbio.gel.gui.views.delegates.selectable_row_delegate import SelectableRowDelegate


class ComboBoxDelegate(SelectableRowDelegate):
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        widget = QComboBox(parent)
        return widget

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        data = index.model().data(index, Qt.EditRole)
        selection = data.get("selection", [])
        value = data.get("value", -1)
        editor.clear()
        selection.sort()
        for txt, v in selection:
            editor.addItem(txt, v)
            if v == value:
                editor.setCurrentIndex(editor.count() - 1)

    def setModelData(
        self, editor: QComboBox, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        data = editor.currentData()
        if data is not None:
            model.setData(index, data, Qt.EditRole)
