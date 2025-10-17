#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QAction, QShowEvent, QHideEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget, QToolBar

from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.gui.models.proxy_table_model import ProxyTableModel
from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.views.table_view import TableView


class MeasurementTypesWidget(QWidget):
    def __init__(
        self,
        model: TableModel,
        toolbar: QToolBar,
        settings: SettingsProxy,
    ):
        super().__init__()
        self.model = model
        view = TableView(model=ProxyTableModel(model=model), settings=settings)
        self.remove_button = QAction("Remove Measurement Type")

        self.remove_button.setVisible(False)
        toolbar.addAction(self.remove_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(view)
        self.setLayout(self.layout)

        self.model.signals.remove_allowed_changed.connect(self.on_remove_allowed_changed)
        self.remove_button.triggered.connect(self.model.remove_current)

        self.on_remove_allowed_changed()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.remove_button.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.remove_button.setVisible(False)

    def on_remove_allowed_changed(self):
        self.remove_button.setEnabled(self.model.remove_allowed)
