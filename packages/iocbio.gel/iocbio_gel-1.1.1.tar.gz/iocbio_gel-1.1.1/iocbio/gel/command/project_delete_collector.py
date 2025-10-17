#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.delete_entity import DeleteEntity
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.command.update_many_relationship import UpdateManyRelationship
from iocbio.gel.db.base import Entity
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.db.entity_visitor import EntityVisitor
from iocbio.gel.domain.project import Project


class ProjectDeleteCollector(EntityVisitor):
    """
    Visitor collecting Projects and their relations for deletion, sorting their deletion commands for a CommandSet
    so their execution order would not cause key constraint violations.
    """

    def __init__(self, db: DatabaseClient, event_registry: EventRegistry):
        self.db = db
        self.commands: list[Command] = []
        self.projects: set[Project] = set()
        self.add_event = event_registry.project_added
        self.delete_event = event_registry.project_deleted
        self.added_to_event = event_registry.added_gel_to_project
        self.removed_from_event = event_registry.removed_gel_from_project

    def visit(self, entity: Entity):
        if not isinstance(entity, Project) or entity in self.projects:
            return

        self.projects.add(entity)

        self.commands.append(DeleteEntity(entity, self.db, self.add_event, self.delete_event))

        if len(entity.gels):
            self.commands.append(
                UpdateManyRelationship(
                    entity,
                    "gels",
                    [],
                    self.db,
                    self.added_to_event,
                    self.removed_from_event,
                )
            )

    def get_command(self) -> Command:
        if len(self.commands) == 1:
            return self.commands[0]

        self.commands.sort(key=self._sort_by_path, reverse=True)

        return TransactionSet(self.commands, self.db)

    @staticmethod
    def _sort_by_path(command: Command) -> tuple[int, str]:
        if isinstance(command, DeleteEntity) and isinstance(command.entity, Project):
            return 0, command.entity.path
        return 1, ""
