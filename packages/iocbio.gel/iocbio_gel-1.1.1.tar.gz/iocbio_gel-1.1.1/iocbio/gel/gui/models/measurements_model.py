#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import List
from PySide6.QtCore import Qt, Slot, QObject, QModelIndex

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.application_state.context import Context, Analysis
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.gui import icons, style
from iocbio.gel.repository.measurement_repository import MeasurementRepository
from iocbio.gel.repository.measurement_type_repository import MeasurementTypeRepository
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.widgets.confirm_popup import ConfirmPopup


class MeasurementsModel(TableModel):
    ATTR = ["id", "type_id", "comment"]
    HEADER = ["ID", "Type", "Comment"]
    TABLE_NAME = "Measurements"
    STRETCH_COLUMNS = [2]
    ITEM_SELECTORS = [0]

    TYPE_INDEX = 1

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        measurement_type_repository: MeasurementTypeRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        self.gel_image = None
        self.measurement_type_repository = measurement_type_repository
        self.measurement_types: dict[int:MeasurementType] = {}
        self.available_types: List[MeasurementType] = []

        super().__init__(
            repository=measurement_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.measurement_added,
            update_event=event_registry.measurement_updated,
            delete_event=event_registry.measurement_deleted,
            select_event=event_registry.measurement_selected,
            parent=parent,
        )

        application_state.context_changed.connect(self.on_context_change)
        self.select_new_on_creation = True

        event_registry.measurement_type_added.connect(self.on_measurement_type_changed)
        event_registry.measurement_type_updated.connect(self.on_measurement_type_changed)
        event_registry.measurement_type_deleted.connect(self.on_measurement_type_changed)
        event_registry.db_connected.connect(self.on_measurement_type_changed)
        event_registry.measurement_added.connect(self.on_measurement_changed)
        event_registry.measurement_deleted.connect(self.on_measurement_changed)
        event_registry.measurement_updated.connect(self.on_measurement_changed)

    def fetch_data(self):
        if self.gel_image is None:
            return []
        return self.repository.fetch_by_image_id(self.gel_image.id)

    def create_new(self):
        if self.gel_image is not None and len(self.available_types) > 0:
            return Measurement(
                gel_id=self.gel_image.gel_id,
                image_id=self.gel_image.id,
                type_id=self.available_types[0].id,
                comment="",
            )
        return None

    def is_ready(self, entity) -> bool:
        return (
            self.gel_image is not None
            and entity.gel_id == self.gel_image.gel_id
            and entity.image_id == self.gel_image.id
            and entity.type_id in [x.id for x in self.available_types]
        )

    def remove_row_accepted(self, row: int, parent: QModelIndex = ...) -> bool:
        measurement = self.current_data[row]
        popup = ConfirmPopup(
            "Delete Measurement",
            f"Are you sure you want to delete Measurement {measurement.measurement_type.name}?",
        )
        return popup.user_confirms()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if (
            index.isValid()
            and role == Qt.DecorationRole
            and index.row() < len(self.current_data)
            and index.column() == 0
        ):
            return icons.SELECT_ROW.pixmap(style.ICON_SIZE)

        if index.isValid() and index.column() == self.TYPE_INDEX:
            entity: Measurement = self.get_entity(index)
            if entity is None:
                return None

            if role == Qt.DisplayRole:
                return self._type_name(entity.type_id)

            elif role == Qt.EditRole:
                selection = list()
                if self.new != entity:
                    selection.append((self._type_name(entity.type_id), entity.type_id))
                selection.extend([(x.name, x.id) for x in self.available_types])
                return dict(value=entity.type_id, selection=selection)

        return super().data(index, role)

    def set_gel_image(self, gel_image: GelImage):
        if self.gel_image == gel_image:
            return

        self.gel_image = gel_image
        self._update_available_types()
        self.reload_data()

        if len(self.current_data) > 0:
            self.event_registry.measurement_selected.emit(self.current_data[0])
        else:
            self.event_registry.measurement_selected.emit(None)

    @Slot(Context)
    def on_context_change(self, context: Context):
        if isinstance(context, Analysis):
            self.set_gel_image(context.image)
        else:
            self.set_gel_image(None)

    @Slot()
    def on_measurement_type_changed(self):
        self.measurement_types = {x.id: x for x in self.measurement_type_repository.fetch_all()}
        self._update_available_types()
        self.reload_data()

    @Slot()
    def on_measurement_changed(self):
        self._update_available_types(reload_on_change=True)

    def _type_name(self, type_id):
        return self.measurement_types.get(type_id, {}).name

    def _update_available_types(self, reload_on_change=False):
        available_types = []
        if self.gel_image is not None:
            available_types = self.repository.get_available_types_for_gel_image(self.gel_image.id)
        if self.available_types != available_types:
            self.available_types = available_types
            if reload_on_change:
                self.reload_data()
