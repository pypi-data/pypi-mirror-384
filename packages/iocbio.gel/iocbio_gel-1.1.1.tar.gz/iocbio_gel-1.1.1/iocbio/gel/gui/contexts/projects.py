#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable

from PySide6.QtCore import Slot, QItemSelectionModel
from PySide6.QtGui import QShowEvent, QAction, QHideEvent
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QToolBar,
    QAbstractItemView,
    QHeaderView,
)

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.gui.models.projects_tree_model import ProjectsTreeModel
from iocbio.gel.gui.views.tree_view import TreeView


class ProjectsWidget(QWidget):
    ADD_ACTION_LABEL = "Add new Project"

    def __init__(
        self,
        application_state: ApplicationState,
        settings: SettingsProxy,
        model: ProjectsTreeModel,
        view_provider: Callable[..., TreeView],
        toolbar: QToolBar,
    ):
        super().__init__()

        self.toolbar = toolbar
        self.application_state = application_state
        self.model = model

        self.add_project = QAction(self.ADD_ACTION_LABEL, self)
        self.add_project.setEnabled(self.application_state.mode is ApplicationMode.EDITING)
        self.add_project.setVisible(False)
        self.add_project.triggered.connect(self._add_project_to_root)
        self.toolbar.addAction(self.add_project)

        self.view = view_provider(
            on_change_event=model.dataChanged, add_action_label=self.ADD_ACTION_LABEL
        )
        self.view.setModel(self.model)
        self.view.setDragEnabled(True)
        self.view.setAcceptDrops(True)
        self.view.setDropIndicatorShown(True)
        self.view.setDragDropMode(QAbstractItemView.InternalMove)
        self.model.modelReset.connect(self.view.expandAll)

        settings_key = f"{self.__class__.__name__}/header"
        self.view.header().restoreState(settings.get(settings_key))
        self.view.header().sectionResized.connect(
            lambda: settings.set(settings_key, self.view.header().saveState())
        )

        self.view.header().setStretchLastSection(False)
        for col in model.STRETCH_COLUMNS:
            self.view.header().setSectionResizeMode(col, QHeaderView.Stretch)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        self.application_state.mode_changed.connect(self.on_edit_mode_changed)

    @Slot(ApplicationMode)
    def on_edit_mode_changed(self, mode: ApplicationMode):
        self.add_project.setEnabled(mode is ApplicationMode.EDITING)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.model.reset_data()
        self.add_project.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.add_project.setVisible(False)

    def _add_project_to_root(self):
        row = self.model.root_item.child_count()
        parent = self.model.root_index
        if self.model.insertRows(row, 1, parent):
            index = self.model.index(row, 0, parent)
            self.view.selectionModel().select(index, QItemSelectionModel.Select)
            self.view.edit(index)
