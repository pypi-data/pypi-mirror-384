#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional, List, Dict

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QShowEvent, QPalette
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyqtgraph import mkPen, ImageItem, HistogramLUTWidget

from iocbio.gel.application.application_state.context import Context, Analysis
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image import Image
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.gui.widgets.analysis_steps.background_subtraction import BackgroundSubtraction
from iocbio.gel.gui.widgets.analysis_steps.curved_line_roi import CurvedLineRoi
from iocbio.gel.repository.gel_image_lane_repository import GelImageLaneRepository
from iocbio.gel.gui.widgets.viewbox_empty_contextmenu import ViewBoxEmptyContextMenu
from iocbio.gel.domain.curved_lane_region import CurvedLaneRegion as LaneRegion


class PassiveLanes(QWidget):
    """
    Widget holding the lanes graph in the "Measurements" tab.
    """

    LANE_WIDTH = 135

    def __init__(
        self,
        event_registry: EventRegistry,
        gel_image_lane_repository: GelImageLaneRepository,
        settings: SettingsProxy,
        application_state: ApplicationState,
    ):
        super().__init__()

        self.settings = settings
        self.application_state = application_state
        self.event_registry = event_registry
        self.gel_image_lane_repository = gel_image_lane_repository

        self.lane_changes_allowed = False
        self.paint_integral_range = True
        self.last_width = self.LANE_WIDTH
        self.gel_image: Optional[GelImage] = None
        self.image_final = None
        self.measurement_id = None

        self.event_registry.gel_image_updated.connect(self.on_image_changed)
        self.event_registry.gel_image_lane_added.connect(self.load_lanes)
        self.event_registry.gel_image_lane_updated.connect(self.load_lanes)
        self.event_registry.gel_image_lane_deleted.connect(self.load_lanes)
        self.event_registry.gel_image_roi_changed.connect(self.load_lanes)
        self.event_registry.gel_lane_updated.connect(self.load_lanes)
        self.event_registry.colormap_changed.connect(self.on_colormap_changed)
        self.event_registry.measurement_lane_updated.connect(self.on_measurement_lane_updated)
        self.event_registry.measurement_selected.connect(self.on_measurement_selected)
        self.application_state.context_changed.connect(self.on_context_change)

        self.layout = QVBoxLayout()

        self.measurement_img = ImageItem()
        self.measurement_img.setZValue(-100)

        self.region = None
        self.regions: List[CurvedLineRoi] = []

        color = self.palette().color(QPalette.AlternateBase).name()
        plot_widget = pg.PlotWidget(title="", background=color, viewBox=ViewBoxEmptyContextMenu())
        plot_widget.invertY(True)
        plot_widget.setAspectLocked(True)
        plot_widget.addItem(self.measurement_img)
        plot_widget.getPlotItem().hideAxis("bottom")
        plot_widget.getPlotItem().hideAxis("left")
        plot_widget.hideButtons()

        vb = plot_widget.getPlotItem().getViewBox()
        vb.add_view_all_action(self, plot_widget)
        vb.add_export_view_action(self, plot_widget)

        self.layout.addWidget(plot_widget)

        self.plot_widget = plot_widget
        self.setLayout(self.layout)

        self.histogram_widget = HistogramLUTWidget()
        self.histogram_widget.item.gradient.loadPreset("grey")

    def new_region(self, lane_region: LaneRegion, gel_image_lane: GelImageLane) -> pg.ROI:
        """
        Creates new CurvedLineRoi object with the last used width.
        """
        roi = CurvedLineRoi(
            lane_region,
            gel_image_lane,
            self.measurement_img,
            self.measurement_id,
            self.on_roi_change,
            self.on_roi_remove,
            self.on_roi_click,
            self.lane_changes_allowed,
            paint_integral_range=self.paint_integral_range,
            pen=mkPen({"color": "#4E8F38", "width": 2, "dash": [1, 8]}),
            handlePen=mkPen({"color": "#FF0000", "width": 2}),
            hoverPen=mkPen({"color": "#FF0000", "width": 2}),
        )

        return roi

    @Slot()
    def on_colormap_changed(self) -> None:
        """
        Apply visual change to the gel image based on colormap settings.
        """
        histogram_state: Optional[Dict[str, any]] = self.settings.get(
            BackgroundSubtraction.SETTINGS_HISTOGRAM_STATE_KEY
        )
        if not histogram_state:
            histogram_state = self.histogram_widget.item.saveState()

        level_min, level_max = histogram_state["levels"]

        histogram_state["levels"] = (level_min, level_max)

        self.histogram_widget.item.restoreState(histogram_state)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.on_image_changed(self.application_state.context.image)

    @Slot(GelImage)
    def on_image_changed(self, gel_image: GelImage) -> None:
        """
        Rebuild the visuals if the gel image has changed.
        """
        if self.application_state.context.image != gel_image:
            return

        if not gel_image or gel_image.image.final is None:
            self.measurement_img.clear()
            self.gel_image = None
            return

        if self.gel_image == gel_image and self.image_final is gel_image.image.final:
            return

        self.gel_image = gel_image
        self.image_final = gel_image.image.final

        self._set_image(self.gel_image.image)

    @Slot(Context)
    def on_context_change(self, context: Context):
        if not isinstance(context, Analysis):
            self.on_image_changed(None)

    def clear_current(self) -> None:
        """
        Clear current lanes from view.
        """
        if self.regions == []:
            return

        for region in self.regions:
            self.plot_widget.removeItem(region)

        self.regions.clear()

    def load_lanes(self):
        """
        Load lanes connected to the gel image to view.
        """
        self.clear_current()
        if self.gel_image is None:
            return True

        lanes: List[GelLane] = self.gel_image.gel.lanes
        unused_gel_lanes = 0
        lanes = sorted(lanes, key=lambda x: x.lane)

        for lane in lanes:
            image_lane: List[GelImageLane] = [
                x for x in lane.gel_image_lanes if x.gel_image == self.gel_image
            ]

            if not image_lane:
                unused_gel_lanes += 1
                continue

            image_lane: GelImageLane = image_lane[0]
            lane_region = image_lane.get_region()
            roi = self.new_region(lane_region, image_lane)

            self.plot_widget.addItem(roi)
            self.regions.append(roi)

            self.last_width = lane_region.width

        return unused_gel_lanes

    def on_roi_click(self, gel_image_lane: GelImageLane):
        """
        Propagate lane selection.
        """
        if self.application_state.mode == ApplicationMode.EDITING:
            self.event_registry.gel_image_lane_selected.emit(gel_image_lane)

    def on_roi_change(self, gel_image_lane: GelImageLane):
        """
        Ignore ROI changes in this view.
        """
        pass

    def on_roi_remove(self, region: pg.ROI):
        self.gel_image_lane_repository.delete(region.gel_image_lane)
        self.plot_widget.removeItem(region)

    def on_measurement_lane_updated(self, measurement_lane: MeasurementLane):
        self.update_integration_region(measurement_lane.image_lane.id)

    def on_measurement_selected(self, measurement: Measurement):
        self.measurement_id = measurement.id if measurement is not None else None
        for region in self.regions:
            region.measurement_id = self.measurement_id
        self.update_integration_region()

    def update_integration_region(self, image_lane_id=None):
        for region in self.regions:
            region.update()

    def _set_image(self, image: Image):
        self.measurement_img.setImage(image.final.T)

        self.on_colormap_changed()
        self.histogram_widget.item.setImageItem(self.measurement_img)
        self.plot_widget.autoRange()

        self.load_lanes()
