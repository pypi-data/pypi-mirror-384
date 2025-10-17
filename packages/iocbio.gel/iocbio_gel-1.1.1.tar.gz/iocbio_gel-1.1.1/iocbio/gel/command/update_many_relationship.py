#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Iterable, Callable

from PySide6.QtCore import SignalInstance

from iocbio.gel.command.command import Command
from iocbio.gel.db.base import Entity
from iocbio.gel.db.database_client import DatabaseClient


class UpdateManyRelationship(Command):
    """
    Command to manage a given relationship list through update undo/redo steps.
    """

    def __init__(
        self,
        entity: Entity,
        relationship: str,
        updated: Iterable[Entity],
        db: DatabaseClient,
        added_to_event: SignalInstance,
        removed_from_event: SignalInstance,
    ):
        self._check_relationship(entity, relationship)
        self.db = db
        self.entity = entity
        self.relationship = relationship
        self.added_to_event = added_to_event
        self.removed_from_event = removed_from_event
        self.added, self.removed = self._difference(getattr(entity, relationship), updated)

    def __repr__(self):
        return f"{self.__class__.__name__}[{self.entity.__class__.__name__}={self.entity.id}]"

    def execute(self) -> list[Callable]:
        return self._update(self.added, self.removed)

    def undo(self) -> list[Callable]:
        return self._update(self.removed, self.added)

    def _update(self, added: list[Entity], removed: list[Entity]) -> list[Callable]:
        for relation in added:
            getattr(self.entity, self.relationship).append(relation)

        for relation in removed:
            getattr(self.entity, self.relationship).remove(relation)

        self.db.commit()

        return [lambda: self.added_to_event.emit(self.entity, x) for x in added] + [
            lambda: self.removed_from_event.emit(self.entity, x) for x in removed
        ]

    @staticmethod
    def _check_relationship(entity: Entity, relationship: str):
        if not hasattr(entity, relationship) or not isinstance(getattr(entity, relationship), list):
            raise TypeError(
                f"{entity.__class__.__name__}.{relationship} is not a valid relationship collection"
            )

    @staticmethod
    def _difference(
        initial: Iterable[Entity], updated: Iterable[Entity]
    ) -> tuple[list[Entity], list[Entity]]:
        added = [x for x in updated if x not in initial]
        removed = [x for x in initial if x not in updated]
        return added, removed
