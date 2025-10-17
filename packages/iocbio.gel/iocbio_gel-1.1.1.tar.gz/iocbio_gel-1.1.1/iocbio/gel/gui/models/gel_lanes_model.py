#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional

from PySide6.QtCore import Slot, Qt, QObject, QModelIndex

from iocbio.gel.application.application_state.context import Context, SingleGel
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.repository.gel_lane_repository import GelLaneRepository
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.widgets.warning_popup import WarningPopup


class GelLanesModel(TableModel):
    ATTR = ["id", "lane", "sample_id", "protein_weight", "is_reference", "comment"]
    HEADER = ["ID", "Lane", "Sample ID", "Protein (μg)", "Reference", "Comment"]
    TABLE_NAME = "Gel Lanes"
    STRETCH_COLUMNS = [5]
    DEFAULT_SORT_FIELD = 1

    PROTEIN_INDEX = 3
    REFERENCE_INDEX = 4

    def __init__(
        self,
        gel_lane_repository: GelLaneRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        self.gel: Optional[Gel] = None
        self.default_sort_field = self.DEFAULT_SORT_FIELD
        super().__init__(
            repository=gel_lane_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.gel_lane_added,
            update_event=event_registry.gel_lane_updated,
            delete_event=event_registry.gel_lane_deleted,
            parent=parent,
        )

        application_state.context_changed.connect(self.on_context_change)

    def fetch_data(self):
        if self.gel is None:
            return []
        return self.repository.fetch_by_gel_id(self.gel.id)

    def is_ready(self, entity: GelLane) -> bool:
        if entity.lane is not None and entity.lane <= 0:
            message = "Gel lane number should be positive. Please correct and try again"
            self.event_registry.set_status_message(message, True)
            WarningPopup("Error on saving", message).exec()
        return entity.lane is not None and entity.lane > 0

    def create_new(self):
        if self.gel is None:
            return None
        return GelLane(
            gel_id=self.gel.id,
            lane=self.gel.get_next_lane(),
            sample_id="0",
            comment="",
            protein_weight=0,
            is_reference=False,
        )

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not self._reference_index(index):
            return super().flags(index)
        if self.edit_allowed:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        return Qt.ItemIsEnabled

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if self._reference_index(index):
            value = super().data(index, Qt.DisplayRole)
            if role == Qt.DisplayRole:
                return "Reference" if value else ""
            if role == Qt.CheckStateRole:
                return Qt.Checked if value else Qt.Unchecked
        return super().data(index, role)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if self._reference_index(index):
            return super().setData(index, True if value > 0 else False, Qt.EditRole)
        return super().setData(index, value, role)

    def set_gel(self, gel: Gel):
        if self.gel != gel:
            self.gel = gel
            self.reload_data()

    @Slot(Context)
    def on_context_change(self, context: Context):
        if isinstance(context, SingleGel):
            self.set_gel(context.gel)
        else:
            self.set_gel(None)

    def _reference_index(self, index: QModelIndex) -> bool:
        return index.isValid() and index.column() == self.REFERENCE_INDEX
