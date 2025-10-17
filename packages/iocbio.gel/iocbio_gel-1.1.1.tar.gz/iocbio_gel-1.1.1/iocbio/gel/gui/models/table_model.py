#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging

from PySide6.QtCore import QObject, Slot, SignalInstance, QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from sqlalchemy import exc

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.db.base import Entity
from iocbio.gel.repository.entity_repository import EntityRepository
from iocbio.gel.gui import icons, style
from iocbio.gel.gui.widgets.warning_popup import WarningPopup
from iocbio.gel.gui.models.tracking_model import TrackingModel


class TableModel(QAbstractTableModel, TrackingModel):
    """
    Base model.

    When deriving, `create_new` and `fetch_data` have to be specialized. Other methods
    that are frequently needed for tailoring the model are `is_ready`, `remove_row_accepted`,
    `flags`, and `data`.
    """

    ATTR = []
    HEADER = []
    TABLE_NAME = "Base"
    STRETCH_COLUMNS = []
    ITEM_SELECTORS = []

    ID_INDEX = 0

    def __init__(
        self,
        repository: EntityRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        add_event: SignalInstance,
        update_event: SignalInstance,
        delete_event: SignalInstance,
        select_event: SignalInstance = None,
        parent: QObject = None,
    ):
        QAbstractTableModel.__init__(self, parent)
        TrackingModel.__init__(self)

        self.repository = repository
        self.application_state = application_state
        self.event_registry = event_registry

        self.current_data = []
        self.new = None
        self.select_new_on_creation = False
        self.selected_row: int = -1
        self.selected_item: Entity = None
        self.select_event = select_event

        self.ignore_update_error = False

        self.reset_new()

        event_registry.db_connected.connect(self.reload_data)
        add_event.connect(self.on_added)
        update_event.connect(self.on_updated)
        delete_event.connect(self.on_deleted)
        if select_event is not None:
            select_event.connect(self.on_selected)
        application_state.mode_changed.connect(self.on_mode_changed)
        self.on_mode_changed(application_state.mode)

    @property
    def add_allowed(self):
        return super().add_allowed and self.new is not None and self.is_ready(self.new)

    @property
    def data_length(self):
        return len(self.current_data)

    def fetch_data(self):
        """
        Default implementation fetches all data from repository
        """
        return self.repository.fetch_all()

    def create_new(self):
        """
        Override in derived class
        """
        return None

    def is_ready(self, entity) -> bool:
        """
        Return True is entity is ready to be inserted as a new one to the database
        """
        return True

    def remove_row_accepted(self, row: int, parent: QModelIndex = ...) -> bool:
        """
        Allows implementing checks before removing row.
        """
        return True

    def reset_new(self):
        self.new = self.create_new()
        self.signals.add_allowed_changed.emit()
        if self.edit_allowed:
            index = self.index(self.rowCount() - 1, 0)
            if index.isValid():
                self.dataChanged.emit(
                    index,
                    self.index(self.rowCount() - 1, self.columnCount() - 1),
                )

    def reload_data(self):
        """
        Load entries upon database connection.
        """
        self.beginResetModel()
        self.current_data = self.fetch_data()
        self.reset_new()
        self.on_current_changed(None)
        self.endResetModel()

    def columnCount(self, parent=None) -> int:
        return len(self.HEADER)

    def rowCount(self, parent=None) -> int:
        return self.data_length + (1 if self.edit_allowed and self.new is not None else 0)

    def get_entity(self, index: QModelIndex) -> Entity:
        if index.isValid():
            row = index.row()
            if row < self.data_length:
                return self.current_data[row]
            elif row == self.data_length:
                return self.new
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role not in [
            Qt.DecorationRole,
            Qt.DisplayRole,
            Qt.EditRole,
            Qt.BackgroundRole,
        ]:
            return None
        if (
            self.edit_allowed
            and self.new is not None
            and index.row() == self.data_length
            and index.column() == self.ID_INDEX
        ):
            if role == Qt.DecorationRole:
                return icons.ADD_ROW.pixmap(style.ICON_SIZE)
            elif role in [Qt.DisplayRole, Qt.EditRole]:
                return "New"
        entity = self.get_entity(index)
        if entity is not None:
            if role in [Qt.DisplayRole, Qt.EditRole]:
                return getattr(entity, self.ATTR[index.column()])
            if role == Qt.BackgroundRole and self.selected_item == entity:
                return QApplication.palette().brush(QPalette.Inactive, QPalette.Midlight)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Default types of the columns. If some special columns are needed, override this
        method to signal it to the decorator of the view.
        """
        if self.edit_allowed and index.column() > self.ID_INDEX:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return super().headerData(section, orientation, role)
        if role != Qt.DisplayRole or section >= self.columnCount():
            return None
        return self.HEADER[section]

    def setData(
        self,
        index: QModelIndex,
        value,
        role: int = Qt.EditRole,
    ) -> bool:
        if not index.isValid() or role != Qt.EditRole or not self.edit_allowed:
            return False

        entity = self.get_entity(index)
        if entity is None:
            return False

        if isinstance(value, str):
            value = value.strip()

        try:
            setattr(entity, self.ATTR[index.column()], value)
            self.dataChanged.emit(index, index)

            if entity.id:
                self.repository.update(entity)
            else:
                self.add_new()
                self.signals.add_allowed_changed.emit()
            return True
        except (exc.SQLAlchemyError, ValueError) as error:
            self._show_unspecified_warning(entity, error)

        return False

    def add_new(self, explicit: bool = False):
        entity = self.new
        if not self.add_allowed:
            return
        try:
            self.repository.add(entity)
            self.reset_new()
            if self.select_new_on_creation:
                self.select_item(len(self.current_data) - 1)
        except (exc.SQLAlchemyError, ValueError) as error:
            self._show_unspecified_warning(entity, error)

    def removeRow(self, row: int, parent: QModelIndex = ...) -> bool:
        if not self.edit_allowed or row > self.data_length:
            return False

        if row == self.data_length:
            self.reset_new()
            return True

        if not self.remove_row_accepted(row, parent):
            return False

        self.beginRemoveRows(QModelIndex(), row, row)
        entity = self.current_data.pop(row)
        self.endRemoveRows()
        self.repository.delete(entity)
        return True

    def remove_current(self):
        if not self.remove_allowed:
            return
        self.removeRow(self.current_row)

    def stretch_columns(self):
        return self.STRETCH_COLUMNS

    def selectable(self, index: QModelIndex) -> bool:
        return index.isValid() and (
            index.column() in self.ITEM_SELECTORS
            or (
                self.edit_allowed
                and self.new is not None
                and index.row() == self.data_length
                and index.column() == self.ID_INDEX
            )
        )

    def select_item(self, row: int):
        if row == self.data_length:
            self.add_new(explicit=True)
            self.signals.add_allowed_changed.emit()
            return
        if self.select_event is None:
            return
        if 0 <= row < self.data_length:
            self.select_event.emit(self.current_data[row])

    @Slot(Entity)
    def on_added(self, entity: Entity):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.current_data.append(entity)
        self.endInsertRows()
        self.dataChanged.emit(
            self.index(self.data_length - 1, 0),
            self.index(self.data_length - 1, self.columnCount() - 1),
        )
        self._update_selected()

    @Slot(int)
    def on_deleted(self, entity_id):
        for index, entity in enumerate(self.current_data):
            if entity.id == entity_id:
                self.beginRemoveRows(QModelIndex(), index, index)
                self.current_data.pop(index)
                self.endRemoveRows()
        if self.current_item is not None and self.current_item.id == entity_id:
            self.on_current_changed(None)
        self._update_selected()

    @Slot(Entity)
    def on_updated(self, entity: Entity):
        try:
            index = self.current_data.index(entity)
            self.dataChanged.emit(self.index(index, 0), self.index(index, self.columnCount() - 1))
        except ValueError as error:
            if self.ignore_update_error:
                return
            logging.getLogger(__name__).warning(
                f"Couldn't find entity in {self.TABLE_NAME}: {error}"
            )
            self.event_registry.set_status_message(
                f"Error: Couldn't find entity in {self.TABLE_NAME}", True
            )
            self.reload_data()

    @Slot(Entity)
    def on_selected(self, entity: Entity):
        self.selected_item = entity
        self._update_selected()

    @Slot(ApplicationMode)
    def on_mode_changed(self, mode: ApplicationMode):
        edit_allowed = mode == ApplicationMode.EDITING
        if edit_allowed != self.edit_allowed:
            self.beginResetModel()
            self.edit_allowed = edit_allowed
            self.endResetModel()
            self.signals.edit_allowed_changed.emit(self.edit_allowed)
            self.on_current_changed(None)
            self.signals.add_allowed_changed.emit()
            self.signals.remove_allowed_changed.emit()

    @Slot(QModelIndex)
    def on_current_changed(self, current_index: QModelIndex):
        item = self.get_entity(current_index) if current_index is not None else None
        if item != self.current_item:
            self.current_item = item
            self.current_row = current_index.row() if item is not None else -1
            self.signals.current_changed.emit()
            self.signals.remove_allowed_changed.emit()

    def _clear_old_selection(self):
        # TODO: This repeating idiom looks like a selected row change - perhaps self._emit_row_change(row_id)?
        index = self.index(self.selected_row, 0)
        if index.isValid():
            self.dataChanged.emit(
                index,
                self.index(self.selected_row, self.columnCount() - 1),
            )
        self.selected_row = -1

    def _update_selected(self):
        if self.selected_item not in self.current_data:
            if self.selected_row >= 0:
                self._clear_old_selection()
                return
            if self.selected_item is not None:
                self.select_event.emit(None)
        else:
            row = self.current_data.index(self.selected_item)
            if row != self.selected_row:
                self._clear_old_selection()
            self.selected_row = row
            self.dataChanged.emit(
                self.index(self.selected_row, 0),
                self.index(self.selected_row, self.columnCount() - 1),
            )

    def _show_unspecified_warning(self, entity, error):
        message = f"Unable to save {entity.__class__.__name__}, change row values and try again"
        self.event_registry.set_status_message(message, True)
        WarningPopup("Error on saving", f"{message}:<br><br>{error}").exec()
