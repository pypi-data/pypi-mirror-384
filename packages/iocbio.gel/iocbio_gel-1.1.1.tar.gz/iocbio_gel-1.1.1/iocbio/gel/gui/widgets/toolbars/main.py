#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Slot
from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PySide6.QtGui import QAction

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.history_manager import HistoryManager


class MainToolbar(QToolBar):
    """
    Toolbar on top of the application.
    """

    MODE_BUTTON_TEXT = {
        ApplicationMode.VIEWING: "Current mode: Viewing",
        ApplicationMode.EDITING: "Current mode: Editing",
    }

    def __init__(
        self,
        event_registry: EventRegistry,
        history_manager: HistoryManager,
        application_state: ApplicationState,
        context_toolbar: QToolBar,
    ):
        super().__init__("Main Toolbar")

        self.event_registry = event_registry
        self.history_manager = history_manager
        self.application_state = application_state
        self.context_toolbar = context_toolbar
        self.controls = QToolBar(self)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(self.spacer)

        self.addWidget(self.context_toolbar)
        self.context_toolbar.addSeparator()
        self.context_toolbar.setStyleSheet("QToolBar::separator { border: none;}")

        self.addSeparator()

        self.undo_action = QAction("Undo", self)
        self.undo_action.setDisabled(True)
        self.undo_action.triggered.connect(self.history_manager.undo)
        self.controls.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setDisabled(True)
        self.redo_action.triggered.connect(self.history_manager.redo)
        self.controls.addAction(self.redo_action)

        self.controls.addSeparator()

        self.mode_switch_action = QAction(self.MODE_BUTTON_TEXT[self.application_state.mode], self)
        self.mode_switch_action.triggered.connect(self.toggle_application_mode)
        self.controls.addAction(self.mode_switch_action)

        self.addWidget(self.controls)

        self.application_state.mode_changed.connect(self.on_edit_mode_changed)
        self.event_registry.history_changed.connect(self.on_history_change)

        self.setMovable(False)
        self.toggleViewAction().setVisible(False)

    def toggle_application_mode(self):
        if self.application_state.mode == ApplicationMode.VIEWING:
            self.application_state.mode = ApplicationMode.EDITING
        else:
            self.application_state.mode = ApplicationMode.VIEWING

    @Slot(ApplicationMode)
    def on_edit_mode_changed(self, mode: ApplicationMode):
        self.mode_switch_action.setText(self.MODE_BUTTON_TEXT[mode])

    @Slot(int, int)
    def on_history_change(self, undo_stack, redo_stack):
        self.undo_action.setEnabled(undo_stack > 0)
        self.redo_action.setEnabled(redo_stack > 0)
