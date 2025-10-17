#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, QModelIndex
from PySide6.QtWidgets import QMessageBox

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.repository.measurement_repository import MeasurementRepository
from iocbio.gel.repository.measurement_type_repository import MeasurementTypeRepository
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.widgets.confirm_popup import ConfirmPopup


class MeasurementTypesModel(TableModel):
    ATTR = ["id", "name", "comment"]
    HEADER = ["ID", "Name", "Comment"]
    TABLE_NAME = "Measurement Types"
    STRETCH_COLUMNS = [2]

    def __init__(
        self,
        measurement_type_repository: MeasurementTypeRepository,
        measurement_repository: MeasurementRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        super().__init__(
            repository=measurement_type_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.measurement_type_added,
            update_event=event_registry.measurement_type_updated,
            delete_event=event_registry.measurement_type_deleted,
            parent=parent,
        )

        self.measurement_repository = measurement_repository

    def is_ready(self, entity) -> bool:
        return len(entity.name) > 0

    def remove_row_accepted(self, row: int, parent: QModelIndex = ...) -> bool:
        entity = self.current_data[row]
        measurement_count = self.measurement_repository.get_count_by_measurement_type_id(entity.id)

        if measurement_count:
            error_message_box = self._create_warning_popup(entity)
            error_message_box.exec()
            return False

        popup = ConfirmPopup(
            "Delete Measurement Type",
            f"Are you sure you want to delete Measurement Type {entity.name}?",
        )
        return popup.user_confirms()

    def create_new(self):
        return MeasurementType(name="", comment="")

    @staticmethod
    def _create_warning_popup(measurement_type):
        box = QMessageBox()
        box.setWindowTitle("Warning")
        box.setText(
            f"Can not delete Measurement Type {measurement_type.name} because there "
            "are related Measurements in the database"
        )
        box.setStandardButtons(QMessageBox.Ok)
        box.setIcon(QMessageBox.Warning)
        return box
