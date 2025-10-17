#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np


from PySide6.QtCore import Slot
from PySide6.QtGui import QShowEvent, QHideEvent, QAction
from PySide6.QtWidgets import QToolBar
from copy import deepcopy
from scipy.interpolate import interp1d


from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.gui.widgets.analysis_steps.passive_lanes import PassiveLanes
from iocbio.gel.repository.gel_image_lane_repository import GelImageLaneRepository
from iocbio.gel.repository.gel_image_repository import GelImageRepository
from iocbio.gel.domain.curved_lane_region import CurvedLaneRegion as LaneRegion


class ActiveLanes(PassiveLanes):
    """
    Widget holding the lanes graph in the "Lanes" tab.
    """

    SYNC_MODE_TEXT = {
        False: "Lane widths: Individual",
        True: "Lane widths: Synced",
    }

    def __init__(
        self,
        event_registry: EventRegistry,
        gel_image_lane_repository: GelImageLaneRepository,
        gel_image_repository: GelImageRepository,
        settings: SettingsProxy,
        application_state: ApplicationState,
        toolbar: QToolBar,
    ):
        super().__init__(event_registry, gel_image_lane_repository, settings, application_state)

        self.gel_image_repository = gel_image_repository
        self.toolbar = toolbar

        self.lane_changes_allowed = True
        self.paint_integral_range = False
        self.unused_gel_lanes = 0

        self.new_lane = QAction("Add new Lane", self)
        self.new_lane.triggered.connect(self.on_new_lane_click)
        self.new_lane.setVisible(False)
        self.toolbar.addAction(self.new_lane)

        self.sync_lanes_widths = QAction(self.SYNC_MODE_TEXT[False], self)
        self.sync_lanes_widths.triggered.connect(self._on_sync_lanes_clicked)
        self.sync_lanes_widths.setVisible(False)
        self.toolbar.addAction(self.sync_lanes_widths)

        self.application_state.mode_changed.connect(self.on_application_state_changed)
        self.event_registry.gel_lane_added.connect(self.on_gel_lane_added)

        self.on_application_state_changed(self.application_state.mode)

    @Slot(GelLane)
    def on_gel_lane_added(self, lane: GelLane):
        if self.gel_image is None or lane is None:
            return
        if lane.gel_id != self.gel_image.gel_id:
            return

        self.unused_gel_lanes = self.gel_image.gel.lanes_count - self.gel_image.lanes_count
        self.on_application_state_changed(self.application_state.mode)

    @Slot(ApplicationMode)
    def on_application_state_changed(self, mode: ApplicationMode):
        """
        Disable graph interactions when not in editing mode.
        """
        allow_editing = mode == ApplicationMode.EDITING
        self.new_lane.setDisabled(not allow_editing or not self.unused_gel_lanes)
        self.sync_lanes_widths.setDisabled(not allow_editing)

        for region in self.regions:
            region.changes_allowed = allow_editing
            region.translatable = allow_editing

    def on_new_lane_click(self):
        """
        Place new lane on the graph.
        """
        gel_image_lane = None
        new_lane_lid = None
        for lane in sorted(self.gel_image.gel.lanes, key=lambda lane: lane.lane):
            if any(x.gel_image == self.gel_image for x in lane.gel_image_lanes):
                continue

            gel_image_lane = GelImageLane(
                gel_id=self.gel_image.gel_id, gel_lane_id=lane.id, image_id=self.gel_image.id
            )
            new_lane_lid = lane.lane
            break

        if gel_image_lane is None:
            return

        # calculate location for a new region

        # step 1: find location of all regions and the closest one
        points = []
        closest_region = None
        for lane in self.gel_image.lanes:
            lid = lane.gel_lane.lane
            reg = lane.get_region()
            points.append([lid, reg.get_coordinates()[0]])
            if closest_region is None or abs(new_lane_lid - closest_region[0]) > abs(
                new_lane_lid - lid
            ):
                closest_region = [lid, reg]

        # step 2: handle different cases
        if len(points) == 0:
            x0 = self.measurement_img.width() // 10
            lane_region = LaneRegion(
                nodes=[[x0, 0], [x0, self.measurement_img.height()]], width=self.last_width
            )
        else:
            lane_region = deepcopy(closest_region[1])
            if len(points) == 1:
                base = lane_region.get_coordinates()[0] + lane_region.width * 1.1
            else:
                spline = interp1d(*np.array(points).T, fill_value="extrapolate")
                base = spline(new_lane_lid)
            if base < 0:
                base = 0
            elif base + lane_region.width * 0.1 > self.measurement_img.width():
                base = self.measurement_img.width() - lane_region.width * 0.1
            lane_region.offset(base - lane_region.get_coordinates()[0], 0)

        gel_image_lane.set_region(lane_region)
        self.gel_image_lane_repository.add(gel_image_lane)

    def load_lanes(self):
        """
        Set new lane button as disabled when lane limit is reached.
        """
        self.unused_gel_lanes = super().load_lanes()
        self.on_application_state_changed(self.application_state.mode)

    def on_roi_click(self, gel_image_lane: GelImageLane):
        """
        Ignoring lane selection in this view.
        """
        pass

    def on_roi_change(self, gel_image_lane: GelImageLane):
        """
        Propagate lane updates to the database.
        Store the width of the lane to assist placing new lanes with the same width.
        """
        if self.application_state.mode != ApplicationMode.EDITING:
            return

        self.last_width = gel_image_lane.width

        if len(self.regions) < 2 or not self.gel_image.sync_lane_widths:
            self.gel_image_lane_repository.update(gel_image_lane)
            return

        command = self.gel_image_repository.get_sync_gel_lanes_command(
            self.gel_image, self.last_width
        )
        self.gel_image_repository.execute(command)

    def on_image_changed(self, gel_image: GelImage) -> None:
        super().on_image_changed(gel_image)
        if self.gel_image:
            self.sync_lanes_widths.setText(self.SYNC_MODE_TEXT[self.gel_image.sync_lane_widths])

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.new_lane.setVisible(True)
        self.sync_lanes_widths.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.new_lane.setVisible(False)
        self.sync_lanes_widths.setVisible(False)

    def _on_sync_lanes_clicked(self) -> None:
        is_synced = not self.gel_image.sync_lane_widths

        self.gel_image.sync_lane_widths = is_synced
        self.sync_lanes_widths.setText(self.SYNC_MODE_TEXT[is_synced])

        if is_synced:
            self.gel_image_repository.update_with_lane_sync(self.gel_image, self.last_width)
        else:
            self.gel_image_repository.update(self.gel_image)
