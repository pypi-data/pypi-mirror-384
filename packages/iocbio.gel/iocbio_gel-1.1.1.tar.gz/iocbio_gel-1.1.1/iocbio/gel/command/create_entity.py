#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Type, Callable

from PySide6.QtCore import SignalInstance

from iocbio.gel.command.command import Command
from iocbio.gel.db.base import Entity
from iocbio.gel.db.database_client import DatabaseClient


class CreateEntity(Command):
    """
    Command to manage entity state through creation undo/redo steps.
    """

    def __init__(
        self,
        entity: Entity,
        db: DatabaseClient,
        add_event: SignalInstance,
        delete_event: SignalInstance,
    ):
        self.db = db
        self.add_event = add_event
        self.delete_event = delete_event

        self.entity_id = None
        self.entity = entity
        self.entity_type: Type[Entity] = entity.__class__
        self.entity_state = entity.get_current_state()

    def __repr__(self):
        return f"{self.__class__.__name__}[{self.entity_type.__name__}]"

    def execute(self) -> list[Callable]:
        if self.entity is None:
            self.entity = self.entity_type()

        self.entity.restore_state(self.entity_state)
        self.entity.id = self.entity_id

        self.db.add(self.entity)
        self.db.commit()

        self.entity.mark_state_saved()
        self.entity_id = self.entity.id
        return [lambda: self.add_event.emit(self.entity)]

    def undo(self) -> list[Callable]:
        self.db.delete(self.entity)
        self.db.commit()
        self.entity = None
        return [lambda: self.delete_event.emit(self.entity_id)]
