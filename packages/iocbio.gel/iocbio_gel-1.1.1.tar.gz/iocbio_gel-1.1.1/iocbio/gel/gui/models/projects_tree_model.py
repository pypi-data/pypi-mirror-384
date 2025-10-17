#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging
from typing import Union, Any, Optional, List

from PySide6.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    Slot,
    Qt,
    QMimeData,
)
from sqlalchemy import exc

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.db.base import Entity
from iocbio.gel.domain.project import Project
from iocbio.gel.gui.models.items.tree_item import TreeItem
from iocbio.gel.gui.models.tree_model import TreeModel
from iocbio.gel.gui.widgets.warning_popup import WarningPopup
from iocbio.gel.repository.project_repository import ProjectRepository


class ProjectsTreeModel(TreeModel):
    COLUMNS = {"name": "Name", "comment": "Comment", "gels_count": "Gels", "path": "Path"}
    EDITABLE_COLUMNS = [0, 1]
    STRETCH_COLUMNS = [1]
    NAME_COLUMN = 0
    PATH_COLUMN = 3

    def __init__(
        self,
        repository: ProjectRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        parent=None,
    ):
        super().__init__(list(self.COLUMNS.values()), application_state, parent=parent)

        self.logger = logging.getLogger(__name__)
        self.repository = repository
        self.event_registry = event_registry

        self.root_id = None
        self.items: dict[int, TreeItem] = dict()
        self.pending_insert = None

        event_registry.project_updated.connect(self._on_updated)
        event_registry.project_added.connect(self._on_added)
        event_registry.project_deleted.connect(self._on_deleted)

    @property
    def is_empty(self):
        return len(self.items) < 2

    def find_by_path(self, path: str) -> Optional[Project]:
        return next(
            (i.entity for i in self.items.values() if i.entity and i.entity.path == path), None
        )

    def reset_data(self, parent: Project = None) -> None:
        if parent:
            self.root_id = parent.id
            self._reset_model(parent.descendants)
        else:
            self.root_id = None
            self._reset_model(self.repository.fetch_all())

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if self.application_state.mode == ApplicationMode.EDITING:
            flags |= Qt.ItemIsDropEnabled

        if index.column() not in self.EDITABLE_COLUMNS:
            flags &= ~Qt.ItemIsEditable

        if flags & Qt.ItemIsEditable:
            flags |= Qt.ItemIsDragEnabled

        return flags

    def setData(
        self, index: Union[QModelIndex, QPersistentModelIndex], value: Any, role: int = ...
    ) -> bool:
        if not super().setData(index, value, role):
            return False

        item: TreeItem = self.get_item(index)
        if item is self.root_item:
            return False

        entity = item.entity if item.entity is not None else self._attach_new_project(item)

        try:
            for i, c in enumerate(self.COLUMNS.keys()):
                if i in self.EDITABLE_COLUMNS:
                    setattr(entity, c, item.data(i))

            if entity.id:
                self.repository.update(entity)
            elif self._is_ready(item):
                self.pending_insert = entity
                self.repository.add(entity)
                item.item_data = self._item_data(entity)
                self.items[entity.id] = item
                self.sort()
            return True
        except (exc.SQLAlchemyError, ValueError) as error:
            self._show_unspecified_warning(entity, error)
        finally:
            self.pending_insert = None

        return False

    def removeRows(self, position: int, rows: int, parent: QModelIndex = QModelIndex()) -> bool:
        if rows > 1:
            return False

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return False

        item = parent_item.child(position)
        if item.entity is None:
            return super().removeRows(position, rows, parent)

        self.beginRemoveRows(parent, position, position + rows - 1)

        if not parent_item.remove_children(position, rows):
            self.endRemoveRows()
            return False

        try:
            self.items.pop(item.entity.id, None)
            self.repository.delete(item.entity)
            return True
        except (exc.SQLAlchemyError, ValueError) as error:
            self.items[item.entity.id] = item
            self._show_unspecified_warning(item.entity, error)
        finally:
            self.endRemoveRows()

        return False

    def mimeTypes(self) -> List[str]:
        return ["text/plain"]

    def mimeData(self, indexes) -> QMimeData:
        mime_data = super().mimeData(indexes)
        if not indexes:
            return mime_data

        item = self.get_item(indexes[0])
        if item is self.root_item or not item.entity.id:
            return mime_data

        mime_data.setText(str(item.entity.id))
        return mime_data

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: Union[QModelIndex, QPersistentModelIndex],
    ) -> bool:
        """
        Always return false to avoid row add/remove calls from parent, using entity update instead.
        """
        if not data.hasText() or not data.text().isdigit():
            return False

        entity_id = int(data.text())
        if entity_id not in self.items:
            return False

        entity = self.items[entity_id].entity
        parent_entity = self.get_item(parent).entity

        try:
            entity.parent_id = None if parent_entity is None else parent_entity.id
            self.repository.update(entity)
        except (exc.SQLAlchemyError, ValueError) as error:
            self._show_unspecified_warning(entity, error)

        return False

    @Slot(Project)
    def _on_updated(self, project: Project) -> None:
        item = self.items.get(project.id, self.root_item)
        if item is self.root_item:
            return

        item.entity = project
        item.item_data = self._item_data(project)

        self.beginResetModel()

        if self._has_moved(item):
            item.parent().child_items.remove(item)
            parent_item = self.items.get(project.parent_id, self.root_item)
            item.parent_item = parent_item
            parent_item.child_items.append(item)

        item.parent().sort(self.NAME_COLUMN, False)
        self.endResetModel()

    @Slot(int)
    def _on_deleted(self, project_id: int) -> None:
        item = self.items.get(project_id, self.root_item)
        if item is self.root_item:
            return

        del self.items[project_id]

        if not self.item_in_tree(item):
            return

        super().removeRows(item.child_number(), 1, self.get_index(item.parent()))

    @Slot(Project)
    def _on_added(self, project: Project) -> None:
        if project == self.pending_insert:
            return
        if self.item_in_tree(self.items.get(project.id, None)):
            return

        parent_item = self.items.get(project.parent_id, self.root_item)
        parent_index = self.get_index(parent_item)
        position = parent_item.child_count()

        self.beginInsertRows(parent_index, position, position)

        item = self._item_from_project(project, parent_item)
        self.items[project.id] = item
        parent_item.child_items.append(item)

        self.endInsertRows()
        self.sort()

    def _reset_model(self, projects: list[Project]) -> None:
        """
        Assumes that the projects are sorted by hierarchy.
        """
        self.beginResetModel()

        self.root_item = TreeItem(self.root_data.copy())
        self.items = {self.root_id: self.root_item}

        for project in projects:
            parent = self.items.get(project.parent_id, self.root_item)
            item = self._item_from_project(project, parent)
            self.items[project.id] = item
            parent.child_items.append(item)

        self.endResetModel()

    def _is_ready(self, item: TreeItem) -> bool:
        return bool(item.data(self.NAME_COLUMN))

    def _item_data(self, entity: Entity) -> list:
        return [getattr(entity, x) for x in self.COLUMNS.keys()]

    def _attach_new_project(self, item: TreeItem) -> Project:
        item.entity = Project()
        if item.parent() and item.parent().entity:
            item.entity.parent_id = item.parent().entity.id
        else:
            item.entity.parent_id = self.root_id

        return item.entity

    def _item_from_project(self, project: Project, parent: TreeItem) -> TreeItem:
        return TreeItem(self._item_data(project), entity=project, parent=parent)

    def _has_moved(self, item: TreeItem) -> bool:
        if item is self.root_item:
            return False

        parent = item.parent()

        if parent is self.root_item:
            return item.entity.parent_id is not None

        return parent.entity.id != item.entity.parent_id

    def _show_unspecified_warning(self, entity: Project, error):
        message = f"Unable to save {entity.__class__.__name__}, change row values and try again"
        self.logger.error(str(error))
        WarningPopup("Error on saving", f"{message}:<br><br>{error}").exec()
