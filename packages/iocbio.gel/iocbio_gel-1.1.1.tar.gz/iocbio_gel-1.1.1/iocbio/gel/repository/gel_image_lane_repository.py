#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.delete_collector import DeleteCollector
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.command.update_entity import UpdateEntity
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.repository.entity_repository import EntityRepository


class GelImageLaneRepository(EntityRepository):
    """
    Gel image lane specific database interactions.
    """

    def __init__(self, db, event_registry: EventRegistry, history_manager: HistoryManager):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.gel_image_lane_updated,
            event_registry.gel_image_lane_added,
            event_registry.gel_image_lane_deleted,
        )
        self.event_registry = event_registry

    def update(self, gel_image_lane: GelImageLane):
        command = self.get_update_command(gel_image_lane)
        if command:
            self.history_manager.execute(command)

    def get_update_command(self, gel_image_lane: GelImageLane) -> Optional[Command]:
        """
        Performs either a single update or a set of updates based on the amount of change.
        A change in region invalidates any work done on the connected lanes, so we delete them.
        A change in zero-line requires a recalculation of the area of connected plots.
        """
        if gel_image_lane.get_saved_state() == gel_image_lane.get_dirty_state():
            return None

        entity_update = UpdateEntity(gel_image_lane, self.db, self.update_event)

        if "region" not in entity_update.after and "zero_line_points" not in entity_update.after:
            return entity_update

        measurement_lanes: list[MeasurementLane] = gel_image_lane.get_updated_measurements()
        if not len(measurement_lanes):
            return entity_update

        commands: list[Command] = [entity_update]
        for measurement_lane in measurement_lanes:
            commands.append(
                UpdateEntity(
                    measurement_lane, self.db, self.event_registry.measurement_lane_updated
                )
            )

        return TransactionSet(commands, self.db)

    def _delete_connected_lanes(self, lanes: list[MeasurementLane]) -> list[Command]:
        visitor = DeleteCollector(self.db, self.event_registry)
        for lane in lanes:
            lane.accept(visitor)

        return visitor.commands
