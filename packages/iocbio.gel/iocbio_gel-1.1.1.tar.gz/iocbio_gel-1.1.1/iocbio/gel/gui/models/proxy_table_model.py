#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Slot, QSortFilterProxyModel, QModelIndex

from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.models.tracking_model import TrackingModel


class ProxyTableModel(QSortFilterProxyModel, TrackingModel):
    def __init__(self, model: TableModel, parent: QObject = None) -> None:
        super().__init__(parent)
        self.setSourceModel(model)
        self.can_sort = True
        self.default_sort_field = getattr(model, "default_sort_field", 0)

    @property
    def current_item(self):
        return self.sourceModel().current_item

    @property
    def current_row(self):
        return self.sourceModel().current_row

    @property
    def edit_allowed(self):
        return self.sourceModel().edit_allowed

    @property
    def settings_key(self):
        model = self.sourceModel()
        return (
            self.__class__.__name__ + "_" + getattr(model, "settings_key", model.__class__.__name__)
        )

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if isinstance(model, TableModel) and source_row == model.data_length:
            return True
        return super().filterAcceptsRow(source_row, source_parent)

    def lessThan(self, source_left: QModelIndex, source_right: QModelIndex) -> bool:
        left = self.sourceModel().data(source_left)
        right = self.sourceModel().data(source_right)
        left = "" if left is None else left
        right = "" if right is None else right
        # Handle mixed types as in the case of IDs
        if isinstance(right, str) and not isinstance(left, str):
            return True
        if isinstance(left, str) and not isinstance(right, str):
            return False
        # Prefer Python native comparison for sorting
        return left < right

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        index = self.index(row, 0, parent)
        source_row = self.mapToSource(index).row()
        return self.sourceModel().removeRow(source_row, parent)

    def select_item(self, row: int):
        self.sourceModel().select_item(self.mapToSource(self.index(row, 0)).row())

    def selectable(self, index: QModelIndex) -> bool:
        return self.sourceModel().selectable(self.mapToSource(index))

    def stretch_columns(self):
        return self.sourceModel().stretch_columns()

    @Slot(QModelIndex)
    def on_current_changed(self, current_index: QModelIndex):
        self.sourceModel().on_current_changed(self.mapToSource(current_index))
