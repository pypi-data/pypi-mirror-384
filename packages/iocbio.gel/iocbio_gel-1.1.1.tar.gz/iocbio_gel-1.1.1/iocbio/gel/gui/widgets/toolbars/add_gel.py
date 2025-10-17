#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Slot
from PySide6.QtGui import QAction

from iocbio.gel.application.application_state.context import Gels, SingleGel
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel import Gel
from iocbio.gel.repository.gel_repository import GelRepository


class AddGel(QAction):
    def __init__(
        self,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        gel_repository: GelRepository,
    ):
        super().__init__("Add new Gel")

        self.event_registry = event_registry
        self.application_state = application_state
        self.gel_repository = gel_repository

        self.triggered.connect(self.on_clicked)
        self.application_state.mode_changed.connect(self.on_edit_mode_changed)

        self.setEnabled(self.application_state.mode is ApplicationMode.EDITING)

    def on_clicked(self):
        gel = Gel(comment="", name="Unnamed gel")
        self.gel_repository.add(gel)

        if self.application_state.project is not None:
            self.gel_repository.update_projects(gel, [self.application_state.project])

        if not isinstance(self.application_state.context, Gels):
            self.application_state.context = SingleGel(gel)

    @Slot(ApplicationMode)
    def on_edit_mode_changed(self, mode):
        self.setEnabled(mode is ApplicationMode.EDITING)
