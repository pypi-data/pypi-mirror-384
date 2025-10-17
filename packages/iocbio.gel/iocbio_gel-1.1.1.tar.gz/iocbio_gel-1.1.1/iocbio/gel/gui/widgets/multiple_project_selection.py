#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional

from PySide6.QtCore import QModelIndex, SignalInstance, Signal
from PySide6.QtWidgets import QComboBox, QTreeView, QWidget

from iocbio.gel.db.base import Entity
from iocbio.gel.domain.project import Project
from iocbio.gel.gui.models.checkbox_proxy import CheckboxProxy
from iocbio.gel.gui.models.projects_tree_model import ProjectsTreeModel


class MultipleProjectSelection(QComboBox):
    DISPLAY_COLUMN = 1
    NOTHING_SELECTED = "Select projects"
    selection_changed: SignalInstance = Signal(dict)

    def __init__(self, model: ProjectsTreeModel, parent: QWidget = None):
        super().__init__(parent)
        self.model = model
        self.view = QTreeView()
        self.checked: dict[int, Entity] = dict()

        self.proxy = CheckboxProxy(self.checked, ProjectsTreeModel.PATH_COLUMN)
        self.proxy.setSourceModel(self.model)
        self.project: Optional[Project] = None

        self.setStyleSheet("QComboBox { combobox-popup: 0; }")

        self.setModel(self.proxy)
        self.setView(self.view)
        self.view.header().setSectionsClickable(True)
        self.setPlaceholderText(self.NOTHING_SELECTED)

        self.setModelColumn(ProjectsTreeModel.PATH_COLUMN)
        for column in range(model.columnCount()):
            if column != ProjectsTreeModel.PATH_COLUMN:
                self.view.hideColumn(column)

        self.view.header().sectionClicked.connect(self._on_header_clicked)
        self.view.pressed.connect(self._on_select)
        self.model.modelReset.connect(self._on_model_changed)
        self.view.expandAll()

    def hidePopup(self) -> None:
        super().hidePopup()
        self.selection_changed.emit(self.checked.keys())

    def set_checked(self, entities: list[Entity]):
        self.checked.clear()
        for entity in entities:
            self.checked[entity.id] = entity
        self._update_placeholder()

    def _on_select(self, index: QModelIndex):
        project: Project = self.model.get_item(index).entity

        if project is None:
            self.checked.clear()
        else:
            if project.id in self.checked:
                del self.checked[project.id]
            else:
                self.checked[project.id] = project

        self.view.viewport().repaint()
        self._update_placeholder()

    def _on_header_clicked(self):
        self.setCurrentIndex(-1)
        self._on_select(self.model.root_index)
        self.hidePopup()

    def _on_model_changed(self):
        self.view.expandAll()
        self.setMinimumWidth(self.view.sizeHint().width())
        self.setCurrentIndex(-1)
        self._update_placeholder()

    def _update_placeholder(self):
        if self.checked:
            self.setPlaceholderText(", ".join(sorted([x.path for x in self.checked.values()])))
        else:
            self.setPlaceholderText(self.NOTHING_SELECTED)
