#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Slot, QDateTime
from PySide6.QtGui import QShowEvent, QAction
from PySide6.QtWidgets import QLabel, QLineEdit, QWidget, QGridLayout, QDateTimeEdit, QSizePolicy

from iocbio.gel.application.application_state.context import Context, SingleGel, Gels
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel import Gel
from iocbio.gel.gui.widgets.confirm_popup import ConfirmPopup
from iocbio.gel.gui.widgets.multiple_project_selection import MultipleProjectSelection
from iocbio.gel.repository.gel_repository import GelRepository


class GelForm(QWidget):
    """
    Widget for changing properties of a single gel.
    TODO: follow GelImageForm implementation for using a model
    """

    DATETIME_FORMAT = "%Y-%m-%d %H:%M"

    def __init__(
        self,
        gel_repository: GelRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        project_selection: MultipleProjectSelection,
    ):
        super().__init__()

        self.gel_repository = gel_repository
        self.event_registry = event_registry
        self.application_state = application_state
        self.gel: Optional[Gel] = None
        self.remove_gel: QAction = QAction("Remove Gel")

        self.ignore_edit = False

        self.name = QLineEdit()
        self.name.editingFinished.connect(self._edit)

        self.ref_time = self._create_time_widget()
        self.ref_time.dateTimeChanged.connect(self._edit)

        self.comment = QLineEdit()
        self.comment.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.comment.setAlignment(Qt.AlignTop)
        self.comment.editingFinished.connect(self._edit)

        self.projects_label = QLabel("Projects: ")
        self.projects = project_selection
        self.projects.selection_changed.connect(self._edit_relations)

        self.remove_gel.triggered.connect(self._on_remove_gel)

        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Name: "), 0, 0, 1, 1)
        self.layout.addWidget(self.name, 0, 1, 1, 1)
        self.layout.addWidget(QLabel("Date and time: "), 1, 0, 1, 1)
        self.layout.addWidget(self.ref_time, 1, 1, 1, 1)
        self.layout.addWidget(self.comment, 0, 2, 2, 1)
        self.layout.addWidget(self.projects_label, 2, 0, 1, 1)
        self.layout.addWidget(self.projects, 2, 1, 1, 2)
        self.layout.setColumnStretch(2, 2)
        self.setLayout(self.layout)

        self._toggle_projects_visibility()

        self.application_state.mode_changed.connect(self._on_edit_mode_change)
        self.application_state.context_changed.connect(self._on_context_change)
        self.event_registry.gel_updated.connect(self._on_gel_updated)
        self.projects.model.dataChanged.connect(self._toggle_projects_visibility)

    def set_gel(self, gel: Gel):
        if not gel or self.gel == gel:
            return

        self.gel = gel
        self._set_from_gel(gel)
        self._on_edit_mode_change(self.application_state.mode)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self.gel:
            self.projects.set_checked(self.gel.projects)
            self._toggle_projects_visibility()

    def _edit(self):
        """
        Propagate form values to database.
        """
        if self.ignore_edit or not self.gel:
            return

        self.gel.name = self.name.text()
        self.gel.comment = self.comment.text()

        date = self.ref_time.dateTime().date()
        time = self.ref_time.dateTime().time()
        self.gel.ref_time = datetime(
            date.year(), date.month(), date.day(), time.hour(), time.minute()
        )

        self.gel_repository.update(self.gel)

    def _edit_relations(self):
        if self.gel:
            self.gel_repository.update_projects(self.gel, self.projects.checked.values())

    def _on_remove_gel(self):
        if not self.remove_gel.isEnabled() or self.gel is None:
            return
        popup = ConfirmPopup("Delete Gel", f"Are you sure you want to delete Gel {self.gel.name}?")
        if not popup.user_confirms():
            return
        gel = self.gel
        self.application_state.context = Gels()
        self.gel_repository.delete(gel)

    @Slot(Context)
    def _on_context_change(self, context: Context):
        if isinstance(context, SingleGel):
            self.set_gel(context.gel)
        else:
            self.set_gel(None)

    @Slot(Gel)
    def _on_gel_updated(self, gel: Gel):
        if self.gel is not None and self.gel == gel:
            self._set_from_gel(gel)

    @Slot(ApplicationMode)
    def _on_edit_mode_change(self, mode: ApplicationMode):
        """
        Disable editing form fields when not in editing mode.
        """
        allow_editing = mode == ApplicationMode.EDITING
        self.name.setEnabled(allow_editing)
        self.comment.setEnabled(allow_editing)
        self.ref_time.setEnabled(allow_editing)
        self.projects.setEnabled(allow_editing)
        self.remove_gel.setEnabled(allow_editing)

    def _set_from_gel(self, gel: Gel):
        self.ignore_edit = True
        self.name.setText(gel.name)
        self.comment.setText(gel.comment)
        self.ref_time.setDateTime(
            QDateTime.fromString(datetime.strftime(gel.ref_time, self.DATETIME_FORMAT), Qt.ISODate)
        )
        self.projects.set_checked(gel.projects)
        self.ignore_edit = False

    def _toggle_projects_visibility(self):
        hidden = self.projects.model.is_empty
        self.projects_label.setHidden(hidden)
        self.projects.setHidden(hidden)

    @staticmethod
    def _create_time_widget():
        widget = QDateTimeEdit(QDateTime.currentDateTime())
        widget.setMaximumDateTime(QDateTime.currentDateTime())
        widget.setCalendarPopup(True)
        return widget
