#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


########################################################################
#
# Copyright (C) 2022 The Qt Company Ltd.
# Contact: https://www.qt.io/licensing/
#
# This file is based on the Qt for Python examples of the Qt Toolkit.
#
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of The Qt Company Ltd nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
#
########################################################################
from typing import Union, Any

from PySide6.QtCore import (
    QModelIndex,
    Qt,
    QAbstractItemModel,
    Signal,
    QPersistentModelIndex,
    SignalInstance,
)

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.gui.models.items.tree_item import TreeItem


class TreeModel(QAbstractItemModel):
    dataChanged: SignalInstance = Signal(QModelIndex, QModelIndex, object)

    def __init__(self, headers: list, application_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.application_state = application_state
        self.root_data = headers
        self.root_item = TreeItem(self.root_data.copy())

    @property
    def root_index(self):
        return QModelIndex()

    def columnCount(self, parent: QModelIndex = None) -> int:
        return self.root_item.column_count()

    def data(self, index: QModelIndex, role: int = None):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        item: TreeItem = self.get_item(index)

        return item.data(index.column())

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        if self.application_state.mode == ApplicationMode.EDITING:
            return Qt.ItemIsEditable | super().flags(index)
        return super().flags(index)

    def get_item(self, index: QModelIndex = QModelIndex()) -> TreeItem:
        if index.isValid():
            item: TreeItem = index.internalPointer()
            if item:
                return item

        return self.root_item

    def get_index(self, item: TreeItem = None) -> QModelIndex:
        if item is None:
            return QModelIndex()
        if item is self.root_item:
            return self.root_index
        return self.createIndex(item.child_number(), 0, item)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root_item.data(section)

        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return QModelIndex()

        child_item: TreeItem = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def insertRows(self, position: int, rows: int, parent: QModelIndex = QModelIndex()) -> bool:
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return False

        self.beginInsertRows(parent, position, position + rows - 1)
        column_count = self.root_item.column_count()
        success: bool = parent_item.insert_children(position, rows, column_count)
        self.endInsertRows()

        return success

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: TreeItem = self.get_item(index)
        if child_item:
            parent_item: TreeItem = child_item.parent()
        else:
            parent_item = None

        if parent_item == self.root_item or not parent_item:
            return QModelIndex()

        return self.get_index(parent_item)

    def removeRows(self, position: int, rows: int, parent: QModelIndex = QModelIndex()) -> bool:
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return False

        self.beginRemoveRows(parent, position, position + rows - 1)
        success: bool = parent_item.remove_children(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return 0
        return parent_item.child_count()

    def setData(
        self, index: Union[QModelIndex, QPersistentModelIndex], value: Any, role: int = ...
    ) -> bool:
        if role != Qt.EditRole:
            return False

        item: TreeItem = self.get_item(index)
        result: bool = item.set_data(index.column(), value)

        if result:
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])

        return result

    def sort(self, column: int = 0, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.beginResetModel()
        self.root_item.sort(column, order == Qt.SortOrder.DescendingOrder)
        self.endResetModel()

    def item_in_tree(self, item: TreeItem) -> bool:
        if item is None:
            return False

        if item is self.root_item:
            return True

        parent_item = item.parent()

        if parent_item is None or item not in parent_item.child_items:
            return False

        return self.item_in_tree(parent_item)
