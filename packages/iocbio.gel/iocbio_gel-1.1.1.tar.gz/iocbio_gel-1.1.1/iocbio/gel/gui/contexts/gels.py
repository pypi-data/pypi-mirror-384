#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable

from PySide6.QtGui import QShowEvent, QHideEvent, QAction
from PySide6.QtWidgets import QVBoxLayout, QWidget, QAbstractItemDelegate, QToolBar

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.gui.models.gels_model import GelsModel
from iocbio.gel.gui.models.projects_tree_model import ProjectsTreeModel
from iocbio.gel.gui.models.proxy_table_model import ProxyTableModel
from iocbio.gel.gui.views.delegates.datetime_delegate import DateTimeDelegate
from iocbio.gel.gui.views.table_view import TableView


class GelsWidget(QWidget):
    def __init__(
        self,
        application_state: ApplicationState,
        gels_model: GelsModel,
        projects_model: ProjectsTreeModel,
        project_selection_delegate: Callable[..., QAbstractItemDelegate],
        toolbar: QToolBar,
        add_gel: QAction,
        settings: SettingsProxy,
    ):
        super().__init__()

        self.application_state = application_state
        self.gels_model = gels_model
        self.projects_model = projects_model

        self.toolbar = toolbar
        self.add_gel = add_gel
        self.remove_gel = QAction("Remove Gel")

        self.add_gel.setVisible(False)
        self.remove_gel.setVisible(False)
        self.toolbar.addAction(self.add_gel)
        self.toolbar.addAction(self.remove_gel)

        self.proxy_model = ProxyTableModel(self.gels_model, self)
        self.view = TableView(model=self.proxy_model, settings=settings)

        self.proxy_model.setFilterKeyColumn(GelsModel.PROJECTS_INDEX)

        self.view.setItemDelegateForColumn(
            GelsModel.TRANSFER_INDEX, DateTimeDelegate(parent=self.view)
        )
        self.view.setItemDelegateForColumn(
            GelsModel.PROJECTS_INDEX, project_selection_delegate(parent=self.view)
        )

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        self.projects_model.dataChanged.connect(self._toggle_projects_visibility)
        self.projects_model.modelReset.connect(self._toggle_projects_visibility)
        self.application_state.project_changed.connect(self._toggle_projects_filter)

        self.gels_model.signals.remove_allowed_changed.connect(self.on_remove_allowed_changed)
        self.remove_gel.triggered.connect(self.gels_model.remove_current)

        self.on_remove_allowed_changed()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._toggle_projects_visibility()
        self._toggle_projects_filter()
        self.add_gel.setVisible(True)
        self.remove_gel.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.add_gel.setVisible(False)
        self.remove_gel.setVisible(False)

    def on_remove_allowed_changed(self):
        self.remove_gel.setEnabled(self.gels_model.remove_allowed)

    def _toggle_projects_visibility(self):
        if self.projects_model.is_empty:
            self.view.hideColumn(GelsModel.PROJECTS_INDEX)
        else:
            self.view.showColumn(GelsModel.PROJECTS_INDEX)

    def _toggle_projects_filter(self):
        if self.application_state.project is None:
            self.proxy_model.setFilterRegularExpression("")
        else:
            path = self.application_state.project.path
            pattern = f"(^{path}$|^{path},|^{path}/|, {path}$|, {path},|, {path}/)"
            self.proxy_model.setFilterRegularExpression(pattern)
