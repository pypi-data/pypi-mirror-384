#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Type

from PySide6 import QtCore
from PySide6.QtCore import QSettings
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedWidget,
    QToolBar,
    QStatusBar,
    QSplitter,
)

from iocbio.gel.const import VERSION
from iocbio.gel.application.application_state.context import (
    Context,
    Gels,
    Analysis,
    SingleGel,
    MeasurementTypes,
    Settings,
    Projects,
)
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.gui.user_resized import UserResized


class MainWindow(QMainWindow, UserResized):
    """
    Main window, switches between views on context change.
    """

    def __init__(
        self,
        history_manager: HistoryManager,
        application_state: ApplicationState,
        settings: QSettings,
        toolbar: QToolBar,
        statusbar: QStatusBar,
        sidebar: QWidget,
        analysis_context: QWidget,
        gels_context: QWidget,
        single_gel_context: QWidget,
        measurement_types_context: QWidget,
        settings_context: QWidget,
        projects_context: QWidget,
    ) -> None:
        super().__init__()
        UserResized.init(self, settings)

        self.application_state = application_state

        self.addToolBar(toolbar)
        self.setStatusBar(statusbar)

        self.contexts: dict[Type[Context], QWidget] = {
            Gels: gels_context,
            Analysis: analysis_context,
            SingleGel: single_gel_context,
            MeasurementTypes: measurement_types_context,
            Settings: settings_context,
            Projects: projects_context,
        }

        self.analysis_context = analysis_context
        self.gels_context = gels_context
        self.single_gel_context = single_gel_context
        self.measurement_types_context = measurement_types_context
        self.settings_context = settings_context
        self.projects_context = projects_context

        self.context_holder = QStackedWidget()

        for widget in self.contexts.values():
            self.context_holder.addWidget(widget)

        splitter = QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.context_holder)

        key = f"{self.size_key}_splitter"
        splitter.restoreState(self.settings.get(key))
        splitter.splitterMoved.connect(lambda: self.settings.set(key, splitter.saveState()))
        splitter.setChildrenCollapsible(False)

        self.setCentralWidget(splitter)

        self.on_context_changed(self.application_state.context)
        self.application_state.context_changed.connect(self.on_context_changed)

        undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo.activated.connect(history_manager.undo)
        redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo.activated.connect(history_manager.redo)

    def on_context_changed(self, context: Context):
        """
        Switch out the active widget in view.
        """
        self.setWindowTitle(f"{context.title} - IOCBIO Gel {VERSION}")

        if context.__class__ not in self.contexts:
            return

        widget = self.contexts[context.__class__]
        self.context_holder.setCurrentWidget(widget)

    def closeEvent(self, event):
        self.save_geometry()
        super(MainWindow, self).closeEvent(event)
