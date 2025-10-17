#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import func, select
from sqlalchemy.sql import Select

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.command.update_entity import UpdateEntity
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.repository.entity_repository import EntityRepository
from iocbio.gel.repository.measurement_lane_repository import MeasurementLaneRepository


class MeasurementRepository(EntityRepository):
    def __init__(
        self,
        db: DatabaseClient,
        event_registry: EventRegistry,
        history_manager: HistoryManager,
        measurement_lane_repository: MeasurementLaneRepository,
    ):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.measurement_updated,
            event_registry.measurement_added,
            event_registry.measurement_deleted,
        )
        self.measurement_lane_repository = measurement_lane_repository

    def fetch_by_gel_id(self, gel_id):
        stmt = select(Measurement).where(Measurement.gel_id == gel_id).order_by(Measurement.id)

        return self.db.execute(stmt).scalars().all()

    def fetch_by_image_id(self, image_id):
        stmt = select(Measurement).where(Measurement.image_id == image_id).order_by(Measurement.id)

        return self.db.execute(stmt).scalars().all()

    def get_count_by_gel_id(self, gel_id):
        stmt = select(func.count()).select_from(Measurement).where(Measurement.gel_id == gel_id)

        return self.db.execute(stmt).scalars().one()

    def get_count_by_measurement_type_id(self, type_id):
        stmt = select(func.count()).select_from(Measurement).where(Measurement.type_id == type_id)

        return self.db.execute(stmt).scalars().one()

    def get_available_types_for_gel_image(self, image_id: int) -> list[MeasurementType]:
        return self._available_types_for_gel_image(select(MeasurementType), image_id).all()

    def count_available_types_for_gel_image(self, image_id: int) -> int:
        return self._available_types_for_gel_image(
            select(func.count()), image_id, order_by=False
        ).one()

    def update_with_lane_sync(self, measurement: Measurement, mn: float, mx: float):
        update_measurement = UpdateEntity(measurement, self.db, self.update_event)
        update_lanes = self.get_sync_gel_lanes_command(measurement, mn, mx)
        self.history_manager.execute(TransactionSet([update_measurement, update_lanes], self.db))

    def get_sync_gel_lanes_command(self, measurement: Measurement, mn: float, mx: float):
        commands = []
        for lane in measurement.active_lanes:
            lane.min = mn
            lane.max = mx
            lane.value = lane.image_lane.calculate_area(mn, mx)
            command = self.measurement_lane_repository.get_update_command(lane)
            if command:
                commands.append(command)

        return TransactionSet(commands, self.db)

    def _available_types_for_gel_image(
        self, select_what: Select, image_id: int, order_by: bool = True
    ):
        join_on = (MeasurementType.id == Measurement.type_id) & (Measurement.image_id == image_id)

        stmt = (
            select_what.select_from(MeasurementType)
            .outerjoin(Measurement, join_on)
            .where(Measurement.id.is_(None))
        )

        if order_by:
            stmt = stmt.order_by(MeasurementType.name)

        return self.db.execute(stmt).scalars()
