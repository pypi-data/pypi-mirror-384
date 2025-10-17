#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Type

from PySide6.QtCore import SignalInstance

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.delete_entity import DeleteEntity
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.db.base import Entity
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.db.entity_visitor import EntityVisitor
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.domain.project import Project


class DeleteCollector(EntityVisitor):
    """
    Visitor collecting Entities for deletion and sorting their deletion commands for a CommandSet
    so their execution order would not cause key constraint violations.
    """

    def __init__(self, db: DatabaseClient, event_registry: EventRegistry):
        self.db = db
        self.event_registry = event_registry
        self.commands: list[Command] = []
        self.entities = set()

        self._type_map: dict[Type[Entity], tuple[SignalInstance, SignalInstance]] = {
            Gel: (event_registry.gel_added, event_registry.gel_deleted),
            GelLane: (event_registry.gel_lane_added, event_registry.gel_lane_deleted),
            GelImage: (event_registry.gel_image_added, event_registry.gel_image_deleted),
            GelImageLane: (
                event_registry.gel_image_lane_added,
                event_registry.gel_image_lane_deleted,
            ),
            MeasurementType: (
                event_registry.measurement_type_added,
                event_registry.measurement_type_deleted,
            ),
            Measurement: (event_registry.measurement_added, event_registry.measurement_deleted),
            MeasurementLane: (
                event_registry.measurement_lane_added,
                event_registry.measurement_lane_deleted,
            ),
            Project: (event_registry.project_added, event_registry.project_deleted),
        }

    def visit(self, entity: Entity):
        if entity.__class__ not in self._type_map or entity in self.entities:
            return

        self.entities.add(entity)

        add_event, delete_event = self._type_map[entity.__class__]

        self.commands.append(DeleteEntity(entity, self.db, add_event, delete_event))

    def get_command(self) -> Command:
        if len(self.commands) == 1:
            return self.commands[0]

        priority = list(self._type_map.keys())

        self.commands.sort(key=lambda x: priority.index(x.entity.__class__), reverse=True)

        return TransactionSet(self.commands, self.db)
