#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import (
    SignalInstance,
    Slot,
    QPoint,
    Qt,
    QModelIndex,
    QItemSelectionModel,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QTreeView, QMenu

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.gui.models.tree_model import TreeModel


class TreeView(QTreeView):
    def __init__(
        self,
        application_state: ApplicationState,
        on_change_event: SignalInstance,
        add_action_label: str,
    ):
        super().__init__()
        self.application_state = application_state
        self.add_action_label = add_action_label

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        on_change_event.connect(self.on_data_changed)
        self.customContextMenuRequested.connect(self.on_custom_context_menu)

    def on_data_changed(self):
        self.viewport().repaint()

    @Slot(QPoint)
    def on_custom_context_menu(self, point: QPoint):
        if not self._should_show_menu(point):
            return

        index = self.indexAt(point)
        model: TreeModel = self.model()
        menu = QMenu(self)

        add_child = QAction(text=self.add_action_label, parent=self)
        add_child.triggered.connect(lambda: self._insert_child_to(model, index))
        menu.addAction(add_child)

        action_delete = QAction(text="Delete", parent=self)
        action_delete.triggered.connect(lambda: self._delete_by(index))
        menu.addAction(action_delete)

        menu.popup(self.viewport().mapToGlobal(point))

    def _should_show_menu(self, point: QPoint):
        return (
            isinstance(self.model(), TreeModel)
            and self.application_state.mode is ApplicationMode.EDITING
            and self.indexAt(point).isValid()
        )

    def _delete_by(self, index: QModelIndex):
        self.model().removeRow(index.row(), self.model().parent(index))

    def _insert_child_to(self, model: TreeModel, parent: QModelIndex):
        item = model.get_item(parent)
        row = item.child_count()
        if model.insertRows(row, 1, parent):
            index = model.index(row, 0, parent)
            self.selectionModel().select(index, QItemSelectionModel.Select)
            self.edit(index)
