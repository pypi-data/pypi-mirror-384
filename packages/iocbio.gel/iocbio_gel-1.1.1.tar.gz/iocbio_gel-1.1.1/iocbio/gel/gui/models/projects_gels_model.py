#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional, Union

from PySide6.QtCore import QModelIndex, Qt, Slot
from PySide6.QtGui import QColor

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.project import Project
from iocbio.gel.gui import icons, style
from iocbio.gel.gui.models.items.tree_item import TreeItem
from iocbio.gel.gui.models.tree_model import TreeModel
from iocbio.gel.repository.gel_repository import GelRepository
from iocbio.gel.repository.project_repository import ProjectRepository


class ProjectsGelsModel(TreeModel):
    def __init__(
        self,
        project_repository: ProjectRepository,
        gel_repository: GelRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent=None,
    ):
        super().__init__(["Name"], application_state, parent=parent)
        self.project_repository = project_repository
        self.gel_repository = gel_repository
        self.event_registry = event_registry

        self.root: Optional[Project] = None
        self.root_id = None
        self.in_hierarchy_projects: dict[int, Project] = dict()
        self.in_tree_projects: dict[int, TreeItem] = dict()
        self.in_tree_gels: dict[int, TreeItem] = dict()

        self.event_registry.added_gel_to_project.connect(self._on_gel_added_to_project)
        self.event_registry.removed_gel_from_project.connect(self._on_gel_removed_from_project)
        self.event_registry.gel_added.connect(self._gel_count_under_root_changed)
        self.event_registry.gel_deleted.connect(self._gel_count_under_root_changed)
        self.event_registry.gel_updated.connect(self._on_gel_renamed)
        self.event_registry.project_updated.connect(self._on_project_updated)
        self.event_registry.project_added.connect(self._on_project_added)
        self.event_registry.project_deleted.connect(self._on_project_removed)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsEnabled

    def data(self, index: QModelIndex, role: int = None):
        if role == Qt.DecorationRole and self._is_project(index):
            return icons.FOLDER.pixmap(style.ICON_SIZE)
        if role == Qt.BackgroundRole and self._is_active_gel(index):
            return QColor(style.SELECTED_GEL_BACKGROUND)
        return super().data(index, role)

    def reset_data(self, parent: Project = None) -> None:
        self.beginResetModel()

        if parent:
            self.root = parent
            self.root_id = parent.id
            self._reset_model(parent.descendants)
        else:
            self.root = None
            self.root_id = None
            self._reset_model(self.project_repository.fetch_all())

        self.endResetModel()

    @Slot(object, object)
    def _on_gel_added_to_project(self, a: Union[Gel, Project], b: Union[Gel, Project]):
        gel, project = (a, b) if isinstance(a, Gel) else (b, a)

        if project.id in self.in_hierarchy_projects:
            self.reset_data(self.root)

    @Slot(object, object)
    def _on_gel_removed_from_project(self, a: Union[Gel, Project], b: Union[Gel, Project]):
        gel, project = (a, b) if isinstance(a, Gel) else (b, a)

        if project.id in self.in_hierarchy_projects or self.root is None:
            self.reset_data(self.root)

    @Slot(Gel)
    def _gel_count_under_root_changed(self, _: Gel):
        if self.root is None:
            self.reset_data(self.root)

    @Slot(Gel)
    def _on_gel_renamed(self, gel: Gel):
        item = self.in_tree_gels.get(gel.id)
        if item is None or item.data(0) == gel.name:
            return
        self.reset_data(self.root)

    @Slot(Project)
    def _on_project_updated(self, project: Project):
        if project.id in self.in_hierarchy_projects:
            self.reset_data(self.root)

    @Slot(Project)
    def _on_project_added(self, project: Project):
        if project.id in self.in_hierarchy_projects:
            return

        if project.parent_id in self.in_hierarchy_projects:
            self.in_hierarchy_projects[project.id] = project

        if project.parent_id not in self.in_tree_projects:
            return

        if len(project.gels):
            self.reset_data(self.root)

    @Slot(int)
    def _on_project_removed(self, project_id: int):
        if project_id == self.root_id:
            self.reset_data(None)
            return

        if project_id in self.in_tree_projects:
            self.reset_data(self.root)

    def _reset_model(self, projects: list[Project]) -> None:
        """
        Assumes that the projects are sorted by hierarchy.
        """
        self.root_item = TreeItem(self.root_data.copy())
        self.in_tree_projects = {self.root_id: self.root_item}
        self.in_hierarchy_projects = {self.root_id: self.root_item}

        for project in projects:
            self.in_hierarchy_projects[project.id] = project
            parent = self.in_tree_projects.get(project.parent_id, self.root_item)
            self._insert_under_parent(project, parent, self.in_tree_projects)

        for project in reversed(projects):
            project_item = self.in_tree_projects[project.id]

            for gel in project.gels:
                self._insert_under_parent(gel, project_item, self.in_tree_gels)

            if not project_item.child_items:
                project_item.parent().child_items.remove(project_item)
                del self.in_tree_projects[project.id]

        gels = self._get_gels()
        for gel in gels:
            self._insert_under_parent(gel, self.root_item, self.in_tree_gels)

    def _get_gels(self):
        if self.root:
            return self.root.gels
        return self.gel_repository.fetch_without_project()

    def _is_project(self, index: QModelIndex) -> bool:
        return index.isValid() and isinstance(self.get_item(index).entity, Project)

    def _is_active_gel(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        entity = self.get_item(index).entity
        return isinstance(entity, Gel) and entity == self.application_state.context.gel

    @staticmethod
    def _insert_under_parent(entity: Union[Gel, Project], parent: TreeItem, collection) -> TreeItem:
        item = TreeItem([entity.name], entity=entity, parent=parent)
        collection[entity.id] = item
        parent.child_items.append(item)
        return item
