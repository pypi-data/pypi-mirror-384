#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, SignalInstance

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.create_entity import CreateEntity
from iocbio.gel.command.delete_collector import DeleteCollector
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.update_entity import UpdateEntity
from iocbio.gel.db.base import Entity
from iocbio.gel.db.database_client import DatabaseClient


class EntityRepository(QObject):
    """
    Base class for common database repository interactions.
    """

    def __init__(
        self,
        db: DatabaseClient,
        history_manager: HistoryManager,
        event_registry: EventRegistry,
        update_event: SignalInstance,
        add_event: SignalInstance,
        delete_event: SignalInstance,
    ):
        super().__init__()
        self.db = db
        self.history_manager = history_manager
        self.event_registry = event_registry
        self.update_event = update_event
        self.add_event = add_event
        self.delete_event = delete_event

    def add(self, entity: Entity):
        self.history_manager.execute(
            CreateEntity(entity, self.db, self.add_event, self.delete_event)
        )

    def update(self, entity: Entity):
        if entity.get_saved_state() != entity.get_dirty_state():
            self.history_manager.execute(UpdateEntity(entity, self.db, self.update_event))

    def delete(self, entity: Entity):
        self.history_manager.execute(self._create_delete_command(entity))

    def execute(self, command: Command) -> None:
        if command is not None:
            self.history_manager.execute(command)

    def _create_delete_command(self, entity: Entity) -> Command:
        visitor = DeleteCollector(self.db, self.event_registry)
        entity.accept(visitor)
        return visitor.get_command()
