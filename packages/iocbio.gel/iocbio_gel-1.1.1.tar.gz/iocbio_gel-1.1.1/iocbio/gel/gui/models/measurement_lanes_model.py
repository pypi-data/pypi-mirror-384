#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Qt, Slot, QObject, QModelIndex

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.repository.measurement_lane_repository import MeasurementLaneRepository
from iocbio.gel.gui.models.table_model import TableModel


class MeasurementLanesModel(TableModel):
    ATTR = ["id", "lane", "value", "is_success", "comment"]
    HEADER = ["ID", "Lane", "Value", "Success", "Comment"]
    TABLE_NAME = "Measurement Lanes"
    STRETCH_COLUMNS = [4]
    DEFAULT_SORT_FIELD = 1

    READ_ONLY_INDICES = [1, 2]
    SUCCESS_INDEX = 3

    def __init__(
        self,
        measurement_lane_repository: MeasurementLaneRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        self.measurement = None
        self.default_sort_field = MeasurementLanesModel.DEFAULT_SORT_FIELD
        super().__init__(
            repository=measurement_lane_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.measurement_lane_added,
            update_event=event_registry.measurement_lane_updated,
            delete_event=event_registry.measurement_lane_deleted,
            parent=parent,
        )

        # As there could be multiple measurements defined for a
        # single gel image, update of gel image lane ROI can trigger
        # measurement lane updates for records not shown in this table.
        # To avoid false error messages, ignore them in self.on_update
        self.ignore_update_error = True

        event_registry.measurement_selected.connect(self.on_measurement_selected)
        event_registry.gel_image_roi_changed.connect(self.reload_data)

    def fetch_data(self):
        if self.measurement is None:
            return []
        data = self.repository.fetch_by_measurement_id(self.measurement.id)
        data.sort(key=lambda x: x.image_lane.gel_lane.lane)
        return data

    def is_ready(self, entity) -> bool:
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid() and index.column() in self.READ_ONLY_INDICES:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.isValid() and index.column() == self.SUCCESS_INDEX:
            if self.edit_allowed:
                return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
            else:
                return Qt.ItemIsEnabled
        return super().flags(index)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if index.isValid() and index.column() == self.SUCCESS_INDEX:
            value = super().data(index, Qt.DisplayRole)
            if role == Qt.DisplayRole:
                return "" if value else "Failed"
            if role == Qt.CheckStateRole:
                return Qt.Checked if value else Qt.Unchecked
        return super().data(index, role)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if index.isValid() and index.column() == self.SUCCESS_INDEX:
            return super().setData(index, True if value > 0 else False, Qt.EditRole)
        return super().setData(index, value, role)

    @Slot(Measurement)
    def on_measurement_selected(self, measurement: Measurement):
        self.measurement = measurement
        self.reload_data()
