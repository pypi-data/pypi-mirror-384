#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import datetime
from typing import Optional

import numpy as np

from PySide6.QtCore import Slot, Qt, QObject, QModelIndex, QLocale

import iocbio.gel.gui.style as style

from iocbio.gel.application.application_state.context import Analysis, Context, SingleGel
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.file_digest import FileDigest
from iocbio.gel.application.image.image import Image
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui import icons
from iocbio.gel.gui.dialogs.select_image_factory import SelectImageFactory
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.widgets.confirm_popup import ConfirmPopup
from iocbio.gel.repository.gel_image_repository import GelImageRepository
from iocbio.gel.repository.image_repository import ImageRepository


class GelImagesModel(TableModel):
    ATTR = ["id", "taken", "measurements"]
    HEADER = ["Image", "Taken", "Measurements"]
    TABLE_NAME = "Gel images"
    ITEM_SELECTORS = [0]

    ICONS = {
        ImageState.MISSING: icons.MISSING_IMAGE,
        ImageState.LOADING: icons.LOADING_IMAGE,
    }

    def __init__(
        self,
        gel_image_repository: GelImageRepository,
        image_repository: ImageRepository,
        dialog_factory: SelectImageFactory,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent: QObject = None,
    ):
        self.gel: Optional[Gel] = None
        self.image_repository = image_repository
        self.image_dialog_factory = dialog_factory

        super().__init__(
            repository=gel_image_repository,
            event_registry=event_registry,
            application_state=application_state,
            add_event=event_registry.gel_image_added,
            update_event=event_registry.gel_image_updated,
            delete_event=event_registry.gel_image_deleted,
            select_event=event_registry.gel_image_selected,
            parent=parent,
        )

        application_state.context_changed.connect(self.on_context_change)
        event_registry.gel_image_added.connect(self.on_gel_image_added)

    def fetch_data(self):
        if self.gel is None:
            return []
        images = self.repository.fetch_by_gel_id(self.gel.id)
        for image in images:
            image.image = self.image_repository.get(image)
        return images

    def create_new(self):
        if self.gel is None:
            return None
        gel_image = GelImage(
            gel_id=self.gel.id,
            hash="",
            taken=datetime.datetime.now(datetime.timezone.utc),
        )
        self.repository.on_init(gel_image)
        return gel_image

    def is_ready(self, entity: GelImage) -> bool:
        return (
            entity is not None
            and entity.hash is not None
            and ((entity.original_file is None) ^ (entity.omero_id is None))
        )

    def remove_row_accepted(self, row: int, parent: QModelIndex = None) -> bool:
        image = self.current_data[row]
        popup = ConfirmPopup(
            "Delete Gel Image", f"Are you sure you want to delete image {image.image.name}?"
        )
        return popup.user_confirms()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        row = index.row()
        if not index.isValid() or row >= self.rowCount() or index.column() != 0:
            return super().data(index, role)

        item: GelImage = self.get_entity(index)
        image: Image = item.image

        if role == Qt.DisplayRole:
            if item.id is not None:
                name = image.name
                taken = QLocale.system().toString(item.taken, QLocale.ShortFormat)
                measurements = ", ".join([m.measurement_type.name for m in item.measurements])
                return f"{name}\n{taken}\n{measurements}"
            else:
                return "Add new image"

        if role == Qt.DecorationRole:
            if item == self.new:
                return icons.ADD_IMAGE.pixmap(style.PREVIEW_ICON_SIZE)
            if image.preview is None:
                return self.ICONS[image.state].pixmap(style.PREVIEW_ICON_SIZE)
            return image.preview

        return super().data(index, role)

    def select_item(self, row: int):
        super().select_item(row)
        item: GelImage = self.get_entity(self.index(row, 0))
        if self.edit_allowed and item == self.new:
            self.replace_image(item)
        if item is None or item.image.state != ImageState.READY:
            return
        if item != self.new:
            self.application_state.context = Analysis(item.gel, item)

    def replace_image(self, entity: GelImage):
        if not self.edit_allowed or entity is None:
            return

        image_selection_dialog = self.image_dialog_factory.create(entity)
        image_selection_dialog.exec()

        if not image_selection_dialog.result():
            return

        image_path = image_selection_dialog.get_path()
        entity.hash = FileDigest.get_hex(image_path)

        if entity.background_is_dark is None:
            image = ImageRepository.get_raw_data(image_path)
            entity.background_is_dark = np.median(image) < np.mean(image)

        if entity == self.new and self.is_ready(entity):
            self.repository.add(entity)
            self.reset_new()
        else:
            self.repository.update(entity)

        self.image_repository.delete(entity.id)
        entity.image = self.image_repository.get(entity)

    def set_gel(self, gel: Gel):
        if self.gel != gel:
            self.gel = gel
            self.reload_data()

    def on_gel_image_added(self, gel_image: GelImage):
        for row, gi in enumerate(self.current_data):
            if gi == gel_image:
                gel_image.image = self.image_repository.get(gel_image)
                self.dataChanged.emit(
                    self.index(row, 0),
                    self.index(row, self.columnCount() - 1),
                )

    @Slot(Context)
    def on_context_change(self, context: Context):
        if isinstance(context, SingleGel):
            self.set_gel(context.gel)
        else:
            self.set_gel(None)
