#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional, List, Callable

from PySide6.QtCore import Slot
from PySide6.QtGui import QShowEvent, QHideEvent, QAction
from PySide6.QtWidgets import QToolBar

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.intensity_plot import IntensityPlot
from iocbio.gel.gui.widgets.analysis_steps.intensity.plot_list import PlotList
from iocbio.gel.repository.measurement_repository import MeasurementRepository
from iocbio.gel.repository.measurement_lane_repository import MeasurementLaneRepository


class MeasurementPlotList(PlotList):
    """
    Scrollable list holding the individual intensity plots in the "Measurements" tab.
    """

    SYNC_MODE_TEXT = {
        False: "Measurement regions: Individual",
        True: "Measurement regions: Synced",
    }

    def __init__(
        self,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        plot_provider: Callable[..., IntensityPlot],
        measurement_repository: MeasurementRepository,
        measurement_lane_repository: MeasurementLaneRepository,
        toolbar: QToolBar,
    ):
        super().__init__(event_registry, application_state)
        self.plot_provider = plot_provider
        self.measurement_repository = measurement_repository
        self.measurement_lane_repository = measurement_lane_repository
        self.toolbar = toolbar

        self.measurement: Optional[Measurement] = None
        self.measurement_id = 0

        self.sync_lanes_roi = QAction(self.SYNC_MODE_TEXT[False], self)
        self.sync_lanes_roi.triggered.connect(self._on_sync_lanes_clicked)
        self.sync_lanes_roi.setVisible(False)
        self.toolbar.addAction(self.sync_lanes_roi)

        self.event_registry.measurement_selected.connect(self._on_measurement_selected)
        self.event_registry.measurement_deleted.connect(self._on_measurement_deleted)
        self.event_registry.gel_image_lane_selected.connect(self._on_lane_selection_change)
        self.event_registry.measurement_lane_added.connect(self._on_lane_added)
        self.event_registry.measurement_lane_deleted.connect(self._on_lane_deleted)
        self.event_registry.measurement_lane_updated.connect(self._on_lane_updated)
        self.application_state.mode_changed.connect(self._on_application_state_changed)

        self._on_application_state_changed(self.application_state.mode)

    def update_plots(self):
        if self._measurement_is_invalid(self.measurement):
            return self.clear_plots()
        super().update_plots()

    def get_plot_regions(self, image) -> List[PlotRegion]:
        """
        Map only those active lanes on the visual plots which are attached to the current measurement.
        """
        regions = super().get_plot_regions(image)

        lanes = {x.image_lane_id: x for x in self.measurement.active_lanes}

        selected = list(filter(lambda x: x.lane.id in lanes, regions))

        return list(map(lambda x: self._apply_range_to_area(x, lanes[x.lane.id]), selected))

    def create_plot(self, region: PlotRegion) -> IntensityPlot:
        """
        Create a plot which monitors the min/max ROI changes.
        """
        return self.plot_provider(
            plot_region=region,
            min_y=self.plot.min_h,
            max_y=self.plot.max_h,
            on_change_callback=self._on_roi_change,
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.sync_lanes_roi.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.sync_lanes_roi.setVisible(False)

    def clear(self) -> None:
        self.sync_lanes_roi.setDisabled(True)
        return super().clear()

    @Slot(ApplicationMode)
    def _on_application_state_changed(self, mode: ApplicationMode):
        allow_editing = mode == ApplicationMode.EDITING
        self.sync_lanes_roi.setDisabled(not allow_editing)

    @Slot(Measurement)
    def _on_measurement_selected(self, measurement: Measurement):
        """
        Change plots when a different measurement is selected.
        """
        if self._measurement_is_invalid(measurement):
            return self.clear()

        if self.measurement == measurement:
            return

        self.measurement = measurement
        self.measurement_id = measurement.id
        self.gel_image = measurement.image
        self.sync_lanes_roi.setText(self.SYNC_MODE_TEXT[self.measurement.sync_lane_rois])
        self._on_application_state_changed(self.application_state.mode)
        self.clear_plots()
        self.update_plots()

    @Slot(int)
    def _on_measurement_deleted(self, measurement_id):
        if self.measurement_id == measurement_id:
            return self.clear()

    @Slot(GelImageLane)
    def _on_lane_selection_change(self, image_lane: GelImageLane):
        """
        Update visible plots when a new lane is attached to the measurement.
        """
        if not self.measurement:
            return self.clear_plots()

        for lane in self.measurement.active_lanes:
            if lane.image_lane_id == image_lane.id:
                self.measurement_lane_repository.delete(lane)
                return

        if self.measurement.sync_lane_rois and len(self.measurement.active_lanes) > 0:
            ref = self.measurement.active_lanes[0]
            min, max = ref.min, ref.max
        else:
            min, max = None, None

        lane = MeasurementLane(
            gel_id=image_lane.gel_id,
            image_id=image_lane.image_id,
            image_lane_id=image_lane.id,
            measurement_id=self.measurement.id,
            min=min,
            max=max,
            value=image_lane.calculate_area(mn=min, mx=max),
            comment="",
            is_success=True,
        )

        self.measurement_lane_repository.add(lane)

    @Slot(MeasurementLane)
    def _on_lane_added(self, lane: MeasurementLane):
        if lane.measurement_id != self.measurement_id:
            return
        self.update_plots()

    @Slot(int)
    def _on_lane_deleted(self, _):
        if self._measurement_is_invalid(self.measurement):
            return
        if len(self.plot.regions) != len(self.measurement.active_lanes):
            self.update_plots()

    @Slot(MeasurementLane)
    def _on_lane_updated(self, lane: MeasurementLane):
        if lane.measurement_id != self.measurement_id:
            return
        self.update_plots()

    def _on_roi_change(self, plot_region: PlotRegion):
        """
        Propagate widget changes to the database.
        """
        lanes = {x.image_lane_id: x for x in self.measurement.active_lanes}
        if plot_region.lane.id not in lanes:
            return

        if self.measurement.sync_lane_rois:
            command = self.measurement_repository.get_sync_gel_lanes_command(
                self.measurement, plot_region.min_limit, plot_region.max_limit
            )
            self.measurement_repository.execute(command)
            return

        changed_lane = lanes[plot_region.lane.id]
        changed_lane.min = plot_region.min_limit
        changed_lane.max = plot_region.max_limit
        changed_lane.value = plot_region.lane.calculate_area(
            plot_region.min_limit, plot_region.max_limit
        )
        self.measurement_lane_repository.update(changed_lane)

    def _on_sync_lanes_clicked(self) -> None:
        if self._measurement_is_invalid(self.measurement):
            return

        is_synced = not self.measurement.sync_lane_rois

        self.measurement.sync_lane_rois = is_synced
        self.sync_lanes_roi.setText(self.SYNC_MODE_TEXT[is_synced])

        if len(self.measurement.active_lanes) > 0 and is_synced:
            ref = self.measurement.active_lanes[0]
            min, max = ref.min, ref.max
            self.measurement_repository.update_with_lane_sync(self.measurement, min, max)
        else:
            self.measurement_repository.update(self.measurement)

    def _replace_image(self, gel_image):
        super()._replace_image(gel_image)
        self.measurement = None

    @staticmethod
    def _apply_range_to_area(
        plot_region: PlotRegion, measurement_lane: MeasurementLane
    ) -> PlotRegion:
        if measurement_lane.min is not None:
            plot_region.min_limit = measurement_lane.min
        if measurement_lane.max is not None:
            plot_region.max_limit = measurement_lane.max
        return plot_region

    @staticmethod
    def _measurement_is_invalid(measurement: Measurement) -> bool:
        return measurement is None or measurement.id is None
