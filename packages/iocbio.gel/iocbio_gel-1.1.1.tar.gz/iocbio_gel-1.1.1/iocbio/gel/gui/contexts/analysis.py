#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Type

from PySide6 import QtCore
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QWidget, QScrollArea, QTabWidget, QSplitter

from iocbio.gel.application.application_state.context import (
    Analysis,
    AnalysisBackground,
    AnalysisRaw,
    AnalysisAdjust,
    AnalysisLanes,
    AnalysisMeasurements,
    Context,
)
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.active_lanes import ActiveLanes
from iocbio.gel.gui.widgets.analysis_steps.adjust import Adjust
from iocbio.gel.gui.widgets.analysis_steps.passive_lanes import PassiveLanes
from iocbio.gel.gui.widgets.analysis_steps.background_subtraction import BackgroundSubtraction
from iocbio.gel.gui.widgets.analysis_steps.raw import Raw
from iocbio.gel.gui.widgets.measurement_lanes import MeasurementLanes
from iocbio.gel.gui.views.table_view import TableView
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.settings_proxy import SettingsProxy


class AnalysisWidget(QTabWidget):
    TAB_CONTEXTS: list[Type[Context]] = [
        AnalysisRaw,
        AnalysisAdjust,
        AnalysisBackground,
        AnalysisLanes,
        AnalysisMeasurements,
    ]

    def __init__(
        self,
        gel_measurements: QWidget,
        raw_image: Raw,
        adjust_image: Adjust,
        passive_lanes: PassiveLanes,
        active_lanes: ActiveLanes,
        background_subtraction: BackgroundSubtraction,
        passive_lane_intensity: QScrollArea,
        active_lane_intensity: QScrollArea,
        measurement_lanes_view: TableView,
        event_registry: EventRegistry,
        settings: SettingsProxy,
        application_state: ApplicationState,
    ):
        super().__init__()

        self.settings_key = f"{self.__module__}.{self.__class__.__name__}"
        self.settings = settings
        self.event_registry = event_registry
        self.application_state = application_state

        lanes_splitter = self._create_lanes_splitter(active_lanes, passive_lane_intensity)

        measurements_splitter = self._create_measurements_splitter(
            passive_lanes, active_lane_intensity, measurement_lanes_view, gel_measurements
        )

        self.addTab(raw_image, "Raw")
        self.addTab(adjust_image, "Adjust")
        self.addTab(background_subtraction, "Background")
        self.addTab(lanes_splitter, "Lanes")
        self.addTab(measurements_splitter, "Measurements")

        self.event_registry.adjust_applied.connect(self.on_adjust_applied)
        self.currentChanged.connect(self.on_tab_change)

    def on_adjust_applied(self):
        """
        Move to background tab after adjusting the image.
        """
        self.setCurrentIndex(self.currentIndex() + 1)

    def on_tab_change(self):
        """
        Emit event to trigger context change.
        """
        previous = self.application_state.context
        self.application_state.context = self.TAB_CONTEXTS[self.currentIndex()].from_context(
            previous
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        current = self.application_state.context
        if current.__class__ != self.TAB_CONTEXTS[self.currentIndex()]:
            if current.__class__ == Analysis:
                image: GelImage = current.image
                if len(image.measurements) > 0:
                    self.setCurrentIndex(self.TAB_CONTEXTS.index(AnalysisMeasurements))
                elif image.lanes_count > 0:
                    self.setCurrentIndex(self.TAB_CONTEXTS.index(AnalysisLanes))
                elif image.background_subtraction is not None:
                    self.setCurrentIndex(self.TAB_CONTEXTS.index(AnalysisBackground))
                else:
                    self.setCurrentIndex(self.TAB_CONTEXTS.index(AnalysisAdjust))
            else:
                self.on_tab_change()

    def _create_lanes_splitter(self, lanes, intensities) -> QSplitter:
        splitter = QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(lanes)
        splitter.addWidget(intensities)
        splitter.setChildrenCollapsible(False)

        self._set_splitter_state_handler(splitter, f"{self.settings_key}/lanes/splitter")

        return splitter

    def _create_measurements_splitter(
        self, image_lanes, intensities, measurement_lanes, measurements
    ) -> QSplitter:
        top = QSplitter(QtCore.Qt.Horizontal)
        top.addWidget(image_lanes)
        top.addWidget(intensities)
        top.setChildrenCollapsible(False)

        bottom = QSplitter(QtCore.Qt.Horizontal)
        bottom.addWidget(MeasurementLanes(measurement_lanes))
        bottom.addWidget(measurements)
        bottom.setChildrenCollapsible(False)

        vertical = QSplitter(QtCore.Qt.Vertical)
        vertical.addWidget(top)
        vertical.addWidget(bottom)
        vertical.setChildrenCollapsible(False)

        splitters = {
            f"{self.settings_key}/measurements/top_splitter": top,
            f"{self.settings_key}/measurements/bottom_splitter": bottom,
            f"{self.settings_key}/measurements/vertical_splitter": vertical,
        }

        for key, splitter in splitters.items():
            self._set_splitter_state_handler(splitter, key)

        return vertical

    def _set_splitter_state_handler(self, splitter: QSplitter, key: str):
        splitter.restoreState(self.settings.get(key))
        splitter.splitterMoved.connect(lambda: self.settings.set(key, splitter.saveState()))
