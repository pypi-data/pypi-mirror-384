#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Any, Optional

from PySide6.QtCore import QIdentityProxyModel, Qt, QModelIndex, QObject

from iocbio.gel.db.base import Entity
from iocbio.gel.gui.models.tree_model import TreeModel


class CheckboxProxy(QIdentityProxyModel):
    def __init__(
        self, checked: dict[int, Entity], column: int, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self.checked = checked
        self.column = column

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "-- NONE --"
        return self.sourceModel().headerData(section, orientation, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.column() == self.column:
            return Qt.ItemIsEnabled
        return self.sourceModel().flags(index)

    def data(self, index: QModelIndex, role: int = None):
        if self._ignore_index(index, role):
            return self.sourceModel().data(index, role)

        model: TreeModel = self.sourceModel()
        entity: Entity = model.get_item(index).entity

        if entity is None:
            return None

        return Qt.Checked if entity.id in self.checked else Qt.Unchecked

    def _ignore_index(self, index: QModelIndex, role: int):
        return (
            index.column() != self.column
            or role != Qt.CheckStateRole
            or not isinstance(self.sourceModel(), TreeModel)
        )
