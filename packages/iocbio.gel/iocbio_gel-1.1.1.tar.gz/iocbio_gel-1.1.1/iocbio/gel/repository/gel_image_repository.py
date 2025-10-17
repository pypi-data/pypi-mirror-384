#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import delete, event, select, exc
from PySide6.QtCore import Slot

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image import Image
from iocbio.gel.command.command import Command
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.command.update_entity import UpdateEntity
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.repository.entity_repository import EntityRepository
from iocbio.gel.repository.gel_image_lane_repository import GelImageLaneRepository


class GelImageRepository(EntityRepository):
    """
    Gel image specific database interactions.
    """

    def __init__(
        self,
        db,
        event_registry: EventRegistry,
        history_manager: HistoryManager,
        image_lane_repository: GelImageLaneRepository,
    ):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.gel_image_updated,
            event_registry.gel_image_added,
            event_registry.gel_image_deleted,
        )

        self.image_lane_repository = image_lane_repository

        event.listen(GelImage, "init", self.on_init)
        event.listen(GelImage, "load", self.on_init)

        event_registry.gel_image_ready.connect(self.on_image_ready)

    def on_init(self, instance, *args, **kwargs):
        instance.image = Image()

    def get(self, image_id):
        return self.db.get(GelImage, image_id)

    def fetch_by_gel_id(self, gel_id):
        stmt = select(GelImage).where(GelImage.gel_id == gel_id).order_by(GelImage.id)

        return self.db.execute(stmt).scalars().all()

    def fetch_by_omero_id(self, omero_id):
        stmt = select(GelImage).where(GelImage.omero_id == omero_id).order_by(GelImage.id)

        return self.db.execute(stmt).scalars().all()

    def delete(self, entity):
        super().delete(entity)
        self.event_registry.measurement_selected.emit(None)

    def update(self, gel_image: GelImage):
        """
        Upstream work is deleted when image ROI is changed.
        User is asked to verify this action since this is too broad of a change to undo.
        """
        entity_update = UpdateEntity(gel_image, self.db, self.update_event)

        if "region" not in entity_update.after and "rotation" not in entity_update.after:
            commands: list[Command] = [entity_update]
            for gel_image_lane in gel_image.lanes:
                for measurement_lane in gel_image_lane.get_updated_measurements():
                    commands.append(
                        UpdateEntity(
                            measurement_lane,
                            self.db,
                            self.event_registry.measurement_lane_updated,
                        )
                    )

            self.history_manager.execute(TransactionSet(commands, self.db))
            self.event_registry.gel_image_selected.emit(gel_image)
            return

        stmt = (
            delete(GelImageLane)
            .where(GelImageLane.image_id == gel_image.id)
            .execution_options(synchronize_session="evaluate")
        )

        transaction = self.db.start_transaction()

        try:
            self.db.execute(stmt)
            entity_update.execute()
            transaction.commit()
            self.db.commit()
        except exc.SQLAlchemyError as error:
            transaction.rollback()
            raise error

        self.event_registry.gel_image_roi_changed.emit(gel_image)
        self.event_registry.gel_image_selected.emit(gel_image)

    def update_with_lane_sync(self, gel_image: GelImage, width: int):
        dirty = gel_image.get_dirty_state()
        if "region" in dirty or "rotation" in dirty:
            self.update(gel_image)
            return

        update_image = UpdateEntity(gel_image, self.db, self.update_event)
        update_lanes = self.get_sync_gel_lanes_command(gel_image, width)

        self.history_manager.execute(TransactionSet([update_image, update_lanes], self.db))

    def get_sync_gel_lanes_command(self, gel_image: GelImage, width: int) -> Command:
        commands = []
        for lane in gel_image.lanes:
            region = lane.get_region()
            region.width = width
            lane.set_region(region)

            command = self.image_lane_repository.get_update_command(lane)
            if command:
                commands.append(command)

        return TransactionSet(commands, self.db)

    @Slot(GelImage, Image)
    def on_image_ready(self, entity: GelImage, image: Image):
        entity.image = image
        self.event_registry.gel_image_updated.emit(entity)
