#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QTableView, QMenu, QHeaderView, QAbstractScrollArea
from PySide6.QtCore import Qt, Slot, Signal, SignalInstance, QObject, QPoint, QModelIndex
from PySide6.QtGui import QAction, QMouseEvent, QKeyEvent

from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.gui.views.delegates.selectable_row_delegate import SelectableRowDelegate


class Signals(QObject):
    highlighted_row_changed: SignalInstance = Signal(int)


class TableView(QTableView):
    def __init__(self, model: TableModel, settings: SettingsProxy):
        super().__init__()
        self.setModel(model)
        self.selection_started: QModelIndex = None
        self.signals = Signals()

        model.selection_model = self.selectionModel()

        self.setItemDelegate(SelectableRowDelegate(self))

        self.verticalHeader().hide()

        sortable = getattr(model, "can_sort", False)
        if sortable:
            sort_field = getattr(model, "default_sort_field", 0)
            self.horizontalHeader().setSortIndicator(sort_field, Qt.AscendingOrder)

        model_settings_key = getattr(model, "settings_key", model.__class__.__name__)
        settings_key = f"{model_settings_key}/{self.__class__.__name__}/horizontal_header"
        self.horizontalHeader().restoreState(settings.get(settings_key))

        def _save_header_state():
            settings.set(settings_key, self.horizontalHeader().saveState())

        self.horizontalHeader().sectionResized.connect(_save_header_state)
        if sortable:
            self.horizontalHeader().sectionClicked.connect(_save_header_state)
            self.setSortingEnabled(True)
        else:
            self.setSortingEnabled(False)

        for col in model.stretch_columns():
            self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.setSelectionMode(QTableView.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_custom_context_menu)

    @Slot(QPoint)
    def on_custom_context_menu(self, point: QPoint):
        index = self.indexAt(point)
        if not index.isValid() or not self.model().edit_allowed:
            return

        menu = QMenu(self)
        action_delete = QAction(text="Delete", parent=self)
        action_delete.triggered.connect(lambda: self.model().removeRow(index.row()))
        menu.addAction(action_delete)
        menu.popup(self.viewport().mapToGlobal(point))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.selection_started is None:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self.indexAt(event.pos())
        if not index.isValid() or event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        model = self.model()
        if model.selectable(index):
            self._set_selected(index)
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.selection_started is None or event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return

        index = self.indexAt(event.pos())
        if not index.isValid():
            self._set_selected()
            return

        model = self.model()
        if index == self.selection_started:
            model.select_item(self.selection_started.row())

        self._set_selected()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        index = self.currentIndex()
        if event.key() != Qt.Key_Return or not index.isValid():
            return super().keyPressEvent(event)

        model = self.model()
        if model.selectable(index):
            model.select_item(index.row())

        return super().keyPressEvent(event)

    def _set_selected(self, index: QModelIndex = None):
        self.selection_started = index
        row = index.row() if index is not None else -1
        self.signals.highlighted_row_changed.emit(row)
        self.viewport().repaint()
