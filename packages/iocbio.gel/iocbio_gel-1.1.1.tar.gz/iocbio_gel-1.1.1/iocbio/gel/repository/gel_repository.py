#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Iterable

from sqlalchemy import select, table, text

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.transaction_set import TransactionSet
from iocbio.gel.command.update_many_relationship import UpdateManyRelationship
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.project import Project
from iocbio.gel.repository.entity_repository import EntityRepository


class GelRepository(EntityRepository):
    def __init__(self, db, event_registry: EventRegistry, history_manager: HistoryManager):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.gel_updated,
            event_registry.gel_added,
            event_registry.gel_deleted,
        )
        self.event_registry = event_registry

    def delete(self, gel: Gel):
        if len(gel.projects) == 0:
            super().delete(gel)
            return

        self.history_manager.execute(
            TransactionSet(
                [self._create_projects_update_command(gel, []), self._create_delete_command(gel)],
                self.db,
            )
        )

    def fetch_all(self):
        stmt = select(Gel).order_by(Gel.id)
        return self.db.execute(stmt).scalars().all()

    def fetch_without_project(self):
        stmt = (
            select(Gel)
            .select_from(Gel)
            .outerjoin(table("gel_to_project"), text("gel.id = gel_to_project.gel_id"))
            .where(text("gel_to_project.gel_id is NULL"))
        ).order_by(Gel.name)
        return self.db.execute(stmt).scalars().all()

    def update_projects(self, gel: Gel, updated_list: Iterable[Project]):
        if gel.projects != list(updated_list):
            self.history_manager.execute(self._create_projects_update_command(gel, updated_list))

    def _create_projects_update_command(self, gel: Gel, updated_list: Iterable[Project]) -> Command:
        return UpdateManyRelationship(
            gel,
            "projects",
            updated_list,
            self.db,
            self.event_registry.added_gel_to_project,
            self.event_registry.removed_gel_from_project,
        )
