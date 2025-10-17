#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import datetime
from typing import Union

from PySide6.QtCore import Qt, Slot, QObject, QModelIndex
from sqlalchemy import exc

from iocbio.gel.application.application_state.context import SingleGel
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.project import Project
from iocbio.gel.gui import icons, style
from iocbio.gel.repository.gel_repository import GelRepository
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.widgets.confirm_popup import ConfirmPopup


class GelsModel(TableModel):
    ATTR = ["id", "name", "ref_time", "comment", "projects", "lanes_count"]
    HEADER = ["ID", "Name", "Date and time", "Comment", "Projects", "Lanes"]
    TABLE_NAME = "Gels"
    STRETCH_COLUMNS = [3]
    ITEM_SELECTORS = [0]

    TRANSFER_INDEX = 2
    PROJECTS_INDEX = 4
    LANES_INDEX = 5

    def __init__(
        self,
        gel_repository: GelRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        super().__init__(
            repository=gel_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.gel_added,
            update_event=event_registry.gel_updated,
            delete_event=event_registry.gel_deleted,
            select_event=event_registry.gel_selected,
            parent=parent,
        )

        event_registry.gel_lane_added.connect(self.on_gel_lane_added)
        event_registry.gel_lane_deleted.connect(self.on_gel_lane_deleted)
        event_registry.added_gel_to_project.connect(self._on_project_count_changed)
        event_registry.removed_gel_from_project.connect(self._on_project_count_changed)

    def is_ready(self, entity: Gel) -> bool:
        if len(entity.name) < 1:
            message = "Gel name should be specified. Please correct and try again"
            self.event_registry.set_status_message(message)
        return len(entity.name) > 0

    def create_new(self):
        return Gel(
            name="",
            ref_time=datetime.datetime.now(),
            comment="",
        )

    def remove_row_accepted(self, row: int, parent: QModelIndex = ...) -> bool:
        gel = self.current_data[row]
        popup = ConfirmPopup("Delete Gel", f"Are you sure you want to delete Gel {gel.name}?")
        return popup.user_confirms()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid() and index.column() == self.LANES_INDEX:
            return Qt.ItemIsEnabled
        if self._is_project_column_of_new_row(index):
            return Qt.ItemIsEnabled
        return super().flags(index)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if self._is_existing_row_icon(index, role):
            return icons.SELECT_ROW.pixmap(style.ICON_SIZE)

        if index.isValid() and index.column() == self.PROJECTS_INDEX:
            entity: Gel = self.get_entity(index)
            if entity is None or entity == self.new:
                return None

            if role == Qt.DisplayRole:
                return ", ".join(sorted([x.path for x in entity.projects]))

            elif role == Qt.EditRole:
                return entity.projects

        if index.isValid() and index.column() == self.LANES_INDEX:
            entity: Gel = self.get_entity(index)
            if entity is None or entity == self.new:
                return None

        return super().data(index, role)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole or not self.edit_allowed:
            return False

        entity = self.get_entity(index)

        if index.column() == self.PROJECTS_INDEX:
            return self._update_projects(entity, value)

        is_existing = entity is not None and entity.id is not None

        result = super().setData(index, value, role)

        if not result or is_existing or self.application_state.project is None:
            return result

        return self._update_projects(entity, [self.application_state.project])

    def add_new(self, explicit: bool = False):
        if explicit and self.new is not None and len(self.new.name) < 1:
            self.new.name = "Unnamed gel"
        return super().add_new(explicit)

    def select_item(self, row: int):
        if row < len(self.current_data):
            self.application_state.context = SingleGel(self.current_data[row])
        super().select_item(row)

    @Slot(GelLane)
    def on_gel_lane_added(self, gel_lane: GelLane):
        for i, g in enumerate(self.current_data):
            if g.id == gel_lane.gel:
                self.dataChanged.emit(
                    self.index(i, self.LANES_INDEX),
                    self.index(i, self.LANES_INDEX),
                )
                break

    @Slot(int)
    def on_gel_lane_deleted(self, _):
        if self.data_length > 0:
            self.dataChanged.emit(
                self.index(0, self.LANES_INDEX),
                self.index(self.data_length, self.LANES_INDEX),
            )

    @Slot(object, object)
    def _on_project_count_changed(self, a: Union[Gel, Project], b: Union[Gel, Project]):
        gel, project = (a, b) if isinstance(a, Gel) else (b, a)
        for i, g in enumerate(self.current_data):
            if g.id == gel.id:
                self.dataChanged.emit(
                    self.index(i, self.PROJECTS_INDEX),
                    self.index(i, self.PROJECTS_INDEX),
                )
                break

    def _is_project_column_of_new_row(self, index: QModelIndex) -> bool:
        return (
            index.isValid()
            and index.column() == self.PROJECTS_INDEX
            and index.row() == len(self.current_data)
        )

    def _is_existing_row_icon(self, index: QModelIndex, role: int) -> bool:
        return (
            index.isValid()
            and role == Qt.DecorationRole
            and index.column() == 0
            and index.row() < len(self.current_data)
        )

    def _update_projects(self, entity: Gel, projects) -> bool:
        if entity is None or entity.id is None:
            return False

        try:
            self.repository.update_projects(entity, projects)
            return True
        except (exc.SQLAlchemyError, ValueError) as error:
            self._show_unspecified_warning(entity, error)
            return False
