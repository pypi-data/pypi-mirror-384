#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Slot

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.zero_line import ZeroLine
from iocbio.gel.gui.widgets.analysis_steps.intensity.intensity_plot import IntensityPlot


class LaneIntensityPlot(IntensityPlot):
    """
    Intensity plot visible on the "Lanes" tab.
    """

    def __init__(
        self,
        plot_region,
        min_y,
        max_y,
        on_change_callback,
        application_state: ApplicationState,
        parent=None,
    ):
        self.application_state = application_state

        super().__init__(plot_region, min_y, max_y, parent)

        self.on_change_callback = on_change_callback
        application_state.mode_changed.connect(self.on_application_state_changed)

    def create_zero_line(self, points) -> ZeroLine:
        """
        Create a modifiable zero-line object.
        """
        zero_line = ZeroLine(
            points,
            is_static=self.application_state.mode != ApplicationMode.EDITING,
            bounds=self._max_bounds(),
        )
        zero_line.sigRegionChangeFinished.connect(self.on_area_change)
        return zero_line

    def set_model(self, plot_region: PlotRegion, min_y, max_y):
        """
        Ignore events from zero-line during data model change.
        """
        self.zero_line.sigRegionChangeFinished.disconnect(self.on_area_change)
        super().set_model(plot_region, min_y, max_y)
        self.zero_line.sigRegionChangeFinished.connect(self.on_area_change)

    def on_area_change(self):
        """
        Make sure the zero-line is within the plot bounds, propagate area change.
        """
        if self.zero_line.is_static:
            return

        self.zero_line.snap_to_bounds()
        points = self.zero_line.as_points()
        self.plot_region.points = points
        self.on_change_callback(self.plot_region)

    @Slot(ApplicationMode)
    def on_application_state_changed(self, mode: ApplicationMode):
        """
        Enable/disable zero-line interactions based on application mode.
        """
        self.zero_line.set_static(mode != ApplicationMode.EDITING)
