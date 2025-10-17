#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Any, Optional

from PySide6.QtCore import (
    QIdentityProxyModel,
    Qt,
    Slot,
)
from PySide6.QtWidgets import QComboBox, QTreeView

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.project import Project
from iocbio.gel.gui.models.projects_tree_model import ProjectsTreeModel


class Proxy(QIdentityProxyModel):
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "-- ALL --"
        return self.sourceModel().headerData(section, orientation, role)


class ProjectSelection(QComboBox):
    PROJECT_KEY = "state/project"

    def __init__(
        self,
        model: ProjectsTreeModel,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        settings: SettingsProxy,
    ):
        super().__init__()
        self.model = model
        self.event_registry = event_registry
        self.application_state = application_state
        self.settings = settings
        self.view = QTreeView()

        self.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.proxy = Proxy()
        self.proxy.setSourceModel(self.model)
        self.project: Optional[Project] = None
        self.project_id = 0

        self.setModel(self.proxy)
        self.setView(self.view)
        self.view.header().setSectionsClickable(True)
        self.setPlaceholderText("Select Project")

        self.setModelColumn(ProjectsTreeModel.PATH_COLUMN)
        for column in range(model.columnCount()):
            if column != ProjectsTreeModel.PATH_COLUMN:
                self.view.hideColumn(column)

        self.activated.connect(self._on_select)
        self.view.header().sectionClicked.connect(self._deselect)
        self.model.modelReset.connect(self._on_model_changed)
        self.model.rowsRemoved.connect(self._on_row_deleted)
        self.event_registry.project_added.connect(lambda: self.setVisible(True))
        self.event_registry.db_connected.connect(self._load_model)
        self.application_state.project_changed.connect(self._on_selected_project_changed)

    def _load_model(self):
        self.model.reset_data()

        project_id = self.settings.get(self.PROJECT_KEY, None)
        if project_id is None or int(project_id) not in self.model.items:
            return

        index = self.model.get_index(self.model.items[int(project_id)])
        self.setRootModelIndex(index.parent())
        self.setCurrentIndex(index.row())
        self._on_select(index.row())

    @Slot(Project)
    def _on_selected_project_changed(self, project: Project):
        if project is None:
            self.settings.remove(self.PROJECT_KEY)
        else:
            self.settings.set(self.PROJECT_KEY, project.id)

    def _on_select(self, index):
        if self.project is None and index < 0:
            return
        elif index < 0:
            self.project = None
            self.project_id = 0
            self.application_state.project = None
            return

        path = self.currentText()
        project = self.model.find_by_path(path)
        if self.project == project:
            return

        self.project = project
        if project is None:
            self.project_id = 0
            self._deselect()
            return

        self.project_id = project.id
        self.application_state.project = project

    def _on_model_changed(self):
        """
        Restore index for current item if the model change has shifted it.
        """
        self.setHidden(self.model.is_empty)
        self.view.expandAll()

        if self.project is None or self.project_id not in self.model.items:
            self._deselect()
            return

        if self.currentText() == self.project.path:
            return

        index = self.model.get_index(self.model.items[self.project.id])
        self.setRootModelIndex(index.parent())
        self.setCurrentIndex(index.row())

    def _on_row_deleted(self):
        self.setHidden(self.model.is_empty)
        if self.project_id and self.project_id not in self.model.items:
            self._deselect()

    def _deselect(self):
        self.setCurrentIndex(-1)
        self.hidePopup()
        self._on_select(-1)
