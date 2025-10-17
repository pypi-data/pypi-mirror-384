#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable

from PySide6.QtWidgets import QWidget, QStyleOptionViewItem
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel

from iocbio.gel.db.base import Entity
from iocbio.gel.gui.views.delegates.selectable_row_delegate import SelectableRowDelegate
from iocbio.gel.gui.widgets.multiple_project_selection import MultipleProjectSelection


class MultiselectDelegate(SelectableRowDelegate):
    def __init__(
        self, select_provider: Callable[..., MultipleProjectSelection], parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.select_provider = select_provider

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = self.select_provider(parent=parent)
        editor.selection_changed.connect(lambda: self.commitData.emit(editor))
        return editor

    def setEditorData(self, editor: MultipleProjectSelection, index: QModelIndex) -> None:
        entities: list[Entity] = index.model().data(index, Qt.EditRole)
        if entities is not None:
            editor.set_checked(entities)

    def setModelData(
        self, editor: MultipleProjectSelection, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        data = editor.checked.values()
        if data is not None:
            model.setData(index, data, Qt.EditRole)
