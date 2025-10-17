#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Qt, QModelIndex, Slot
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QButtonGroup,
    QPushButton,
    QTreeView,
    QComboBox,
    QFileDialog,
    QStyle,
)
from pathlib import Path

from iocbio.gel.application.application_state.context import (
    Context,
    Gels,
    MeasurementTypes,
    SingleGel,
    Projects,
    Settings,
)
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.xls_writer import XlsWriter
from iocbio.gel.gui.models.projects_gels_model import ProjectsGelsModel
from iocbio.gel.gui.widgets.warning_popup import WarningPopup


class Sidebar(QWidget):
    """
    Gels overview list and navigation buttons visible on the left side of the application.
    """

    SETTINGS_EXPORT_PATH_KEY = "Export/path"

    def __init__(
        self,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        project_selection: QComboBox,
        model: ProjectsGelsModel,
        writer: XlsWriter,
        documents_path: str,
        settings: SettingsProxy,
    ):
        super().__init__()

        self.event_registry = event_registry
        self.application_state = application_state
        self.model = model
        self.view = QTreeView(parent=self)
        self.writer = writer
        self.documents_path = documents_path
        self.settings = settings
        self._passive_mode = False

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)

        self.buttons = {
            Gels: QPushButton("Gels"),
            Projects: QPushButton("Projects"),
            MeasurementTypes: QPushButton("Types"),
            Settings: QPushButton("Settings"),
        }

        self.button_group = QButtonGroup()

        self.layout.addWidget(self.buttons[Gels])

        self.project_selection = project_selection
        self.layout.addWidget(self.project_selection)

        self.view.setModel(self.model)
        self.view.setHeaderHidden(True)
        self.view.clicked.connect(self._on_gel_clicked)
        self.model.dataChanged.connect(lambda: self.view.viewport().repaint())
        self.model.modelReset.connect(self.view.expandAll)
        self.layout.addWidget(self.view, stretch=100)

        self.layout.addWidget(self.buttons[Projects], 1, Qt.AlignBottom)

        self.layout.addWidget(self.buttons[MeasurementTypes], 1, Qt.AlignBottom)

        self.layout.addWidget(self.buttons[Settings])

        export_button = QPushButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Export"
        )
        export_button.clicked.connect(self._export)
        self.layout.addWidget(export_button)

        self.setLayout(self.layout)

        self.button_id_to_context = dict()
        for index, context in enumerate(self.buttons.keys()):
            button = self.buttons[context]
            self.button_group.addButton(button, index)
            button.setCheckable(True)
            self.button_id_to_context[index] = context

        self.button_group.idToggled.connect(self._on_button_toggled)
        self.event_registry.db_connected.connect(self._load_model)
        self.application_state.project_changed.connect(self._load_model)
        self.application_state.context_changed.connect(self._on_context_change)

        self._on_context_change(self.application_state.context)

    def _on_gel_clicked(self, index: QModelIndex):
        item = self.model.get_item(index)
        if isinstance(item.entity, Gel):
            self._navigate(SingleGel(item.entity))

    def _navigate(self, context: Context):
        self.application_state.context = context

    def _load_model(self):
        self.model.reset_data(self.application_state.project)

    def _export(self):
        file_path = None
        try:
            path = self.settings.get(self.SETTINGS_EXPORT_PATH_KEY, self.documents_path)
            dialog = QFileDialog(caption="Save File", directory=path, filter="Excel (*.xlsx)")
            dialog.setDefaultSuffix("xlsx")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setFileMode(QFileDialog.AnyFile)
            if dialog.exec():
                file_path = dialog.selectedFiles()[0]
                self.writer.write(file_path)
                self.settings.set(
                    self.SETTINGS_EXPORT_PATH_KEY, str(Path(file_path).resolve().parent)
                )

        except Exception as error:
            message = f"Unable to write export to file {file_path}"
            WarningPopup("Error on export", f"{message}:<br><br>{error}").exec()

    def _set_button_checked(self, index: int):
        self._passive_mode = True
        if index >= 0:
            self.button_group.button(index).setChecked(True)
        elif self.button_group.checkedButton():
            self.button_group.setExclusive(False)
            self.button_group.checkedButton().setChecked(False)
            self.button_group.setExclusive(True)
        self._passive_mode = False

    def _on_button_toggled(self, index: int, toggled: bool):
        if not toggled or self._passive_mode:
            return
        self._navigate(self.button_id_to_context[index]())

    @Slot(Context)
    def _on_context_change(self, context):
        self.view.viewport().repaint()

        for index, context_class in enumerate(self.buttons.keys()):
            if isinstance(context, context_class):
                self._set_button_checked(index)
                return

        self._set_button_checked(-1)

    @staticmethod
    def _set_style(button: QPushButton, is_active: bool):
        button.setStyleSheet("QPushButton { font-weight: bold; };" if is_active else "")
