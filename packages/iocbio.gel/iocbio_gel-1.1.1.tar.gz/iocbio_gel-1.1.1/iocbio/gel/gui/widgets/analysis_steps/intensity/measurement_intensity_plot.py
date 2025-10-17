#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import pyqtgraph as pg
from PySide6 import QtGui
from PySide6.QtCore import Slot

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.zero_line import ZeroLine
from iocbio.gel.gui.widgets.analysis_steps.intensity.intensity_plot import IntensityPlot


class MeasurementIntensityPlot(IntensityPlot):
    """
    Intensity plot visible on the "Measurements" tab.
    """

    TRANSPARENT = QtGui.QBrush(QtGui.QColor(255, 255, 255, 0))

    def __init__(
        self,
        plot_region: PlotRegion,
        min_y,
        max_y,
        on_change_callback,
        application_state: ApplicationState,
        parent=None,
    ):
        super().__init__(plot_region, min_y, max_y, parent)

        self.on_change_callback = on_change_callback
        application_state.mode_changed.connect(self.on_application_state_changed)

        self.roi = pg.LinearRegionItem(
            [plot_region.min_limit, plot_region.max_limit],
            bounds=[0, self.max_x],
            movable=application_state.mode == ApplicationMode.EDITING,
            brush=self.TRANSPARENT,
            pen=pg.mkPen({"color": "#fc8403", "width": 1, "dash": [3, 4]}),
            hoverPen=pg.mkPen({"color": "#fc8403", "width": 1.5}),
            swapMode="sort",
        )

        self.roi.sigRegionChangeFinished.connect(self.on_area_change)
        self.addItem(self.roi)

    def create_zero_line(self, points) -> ZeroLine:
        """
        Create a static zero-line object.
        """
        return ZeroLine(points, is_static=True)

    def set_model(self, plot_region: PlotRegion, min_y, max_y):
        """
        Ignore min/max ROI changes during data model change.
        Move min/max ROI lines to match data.
        """
        self.roi.sigRegionChangeFinished.disconnect(self.on_area_change)
        super().set_model(plot_region, min_y, max_y)
        self.roi.lines[0].setPos((plot_region.min_limit, 0))
        self.roi.lines[1].setPos((plot_region.max_limit, 0))
        self.roi.setBounds([0, self.max_x])
        self.roi.sigRegionChangeFinished.connect(self.on_area_change)

    def on_area_change(self):
        """
        Propagate area change.
        """
        self.plot_region.min_limit, self.plot_region.max_limit = self.roi.getRegion()
        self.on_change_callback(self.plot_region)

    @Slot(ApplicationMode)
    def on_application_state_changed(self, mode: ApplicationMode):
        """
        Enable/disable ROI interactions based on application mode.
        """
        self.roi.setMovable(mode == ApplicationMode.EDITING)
