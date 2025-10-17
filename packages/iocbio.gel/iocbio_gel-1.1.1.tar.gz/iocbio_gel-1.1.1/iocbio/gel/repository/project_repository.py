#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import select

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.command.project_delete_collector import ProjectDeleteCollector
from iocbio.gel.command.update_project import UpdateProject
from iocbio.gel.domain.project import Project
from iocbio.gel.repository.entity_repository import EntityRepository


class ProjectRepository(EntityRepository):
    def __init__(self, db, event_registry: EventRegistry, history_manager: HistoryManager):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.project_updated,
            event_registry.project_added,
            event_registry.project_deleted,
        )
        self.event_registry = event_registry

    def update(self, project: Project):
        if project.get_saved_state() == project.get_dirty_state():
            return
        self.history_manager.execute(UpdateProject(project, self.db, self.update_event))

    def delete(self, project: Project):
        visitor = ProjectDeleteCollector(self.db, self.event_registry)
        project.accept(visitor)
        self.history_manager.execute(visitor.get_command())

    def fetch_all(self) -> list[Project]:
        stmt = select(Project).order_by(Project.path)
        return self.db.execute(stmt).scalars().all()
