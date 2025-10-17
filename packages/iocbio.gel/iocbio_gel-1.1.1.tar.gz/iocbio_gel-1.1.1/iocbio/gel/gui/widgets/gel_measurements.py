#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QShowEvent, QHideEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QToolBar

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.gui.models.measurements_model import MeasurementsModel
from iocbio.gel.gui.models.proxy_table_model import ProxyTableModel
from iocbio.gel.gui.views.delegates.combobox_delegate import ComboBoxDelegate
from iocbio.gel.gui.views.table_view import TableView


class GelMeasurements(QWidget):
    """
    Container holding the measurements' table in the "Measurements" tab.
    """

    def __init__(
        self,
        application_state: ApplicationState,
        event_registry: EventRegistry,
        measurements_model: MeasurementsModel,
        toolbar: QToolBar,
        settings: SettingsProxy,
    ):
        super().__init__()
        self.application_state = application_state
        self.model = measurements_model
        self.view = TableView(model=ProxyTableModel(model=measurements_model), settings=settings)
        self.add_measurement = QAction("Add new Measurement")
        self.remove_measurement = QAction("Remove Measurement")
        self.toolbar = toolbar

        self.add_measurement.setVisible(False)
        self.remove_measurement.setVisible(False)
        self.toolbar.addAction(self.add_measurement)
        self.toolbar.addAction(self.remove_measurement)
        self.view.setItemDelegateForColumn(
            MeasurementsModel.TYPE_INDEX, ComboBoxDelegate(parent=self.view)
        )

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h2>Measurements</h2>"))
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        event_registry.measurement_selected.connect(self.on_measurement_selected)
        self.model.signals.add_allowed_changed.connect(self.on_add_allowed_changed)
        self.model.signals.remove_allowed_changed.connect(self.on_remove_allowed_changed)
        self.add_measurement.triggered.connect(lambda: self.model.add_new(True))
        self.remove_measurement.triggered.connect(self.model.remove_current)

        self.on_add_allowed_changed()
        self.on_remove_allowed_changed()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.add_measurement.setVisible(True)
        self.remove_measurement.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.add_measurement.setVisible(False)
        self.remove_measurement.setVisible(False)

    @Slot(Measurement)
    def on_measurement_selected(self, measurement: Measurement):
        self.application_state.context.measurement = measurement

    @Slot()
    def on_add_allowed_changed(self):
        self.add_measurement.setEnabled(self.model.add_allowed)

    @Slot()
    def on_remove_allowed_changed(self):
        self.remove_measurement.setEnabled(self.model.remove_allowed)
