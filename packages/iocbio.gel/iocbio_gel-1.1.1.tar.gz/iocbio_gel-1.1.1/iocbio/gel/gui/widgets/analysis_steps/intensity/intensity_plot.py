#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import pyqtgraph as pg
import numpy as np

from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.zero_line import ZeroLine
from iocbio.gel.gui.widgets.viewbox_empty_contextmenu import ViewBoxEmptyContextMenu


class IntensityPlot(pg.PlotWidget):
    """
    Base class for the widgets displaying the individual intensity plots.
    """

    def __init__(self, plot_region: PlotRegion, min_y, max_y, parent=None):
        pg.PlotWidget.__init__(self, parent, background="white", viewBox=ViewBoxEmptyContextMenu())

        self.setLimits(minXRange=50, minYRange=50)

        self.plot_region = plot_region
        self.min_y = min_y
        self.max_y = max_y
        self.min_x, self.max_x = plot_region.lane.get_region_range()

        self.setYRange(min_y, max_y)
        self._graph_pen = pg.mkPen({"color": "#005AEB", "width": 2})
        self.intensities_graph = self.plot(
            list(range(0, len(self.plot_region.intensities))),
            self.plot_region.intensities,
            pen=self._graph_pen,
        )

        self.zero_line = self.create_zero_line(plot_region.points)
        self.addItem(self.zero_line)

        vb = self.getPlotItem().getViewBox()
        vb.add_view_all_action(self, self)
        vb.add_export_view_action(self, self)

    def set_model(self, plot_region: PlotRegion, min_y, max_y):
        """
        Change visuals to match new plot region.
        """
        if self.min_y != min_y or self.max_y != self.max_y:
            self.setYRange(min_y, max_y)
            self.min_y = min_y
            self.max_y = max_y

        self.min_x, self.max_x = plot_region.lane.get_region_range()

        if self.plot_region.lane_id != plot_region.lane_id:
            self.setYRange(min_y, max_y)
            self.setXRange(0, self.max_x)

        self.plot_region = plot_region

        x_range = list(range(0, len(self.plot_region.intensities)))
        y_range = self.plot_region.intensities
        if self._intensities_changed(self.intensities_graph.getData(), [x_range, y_range]):
            self.removeItem(self.intensities_graph)
            self.intensities_graph = self.plot(x_range, y_range, pen=self._graph_pen)

        points = plot_region.points
        if not np.array_equal(points, self.zero_line.as_points()):
            self.zero_line.setPoints(points)

        self.zero_line.maxBounds = self._max_bounds()

    def create_zero_line(self, points) -> ZeroLine:
        """
        To be implemented by children.
        """
        pass

    def update_title(self):
        """
        Update the visual title on the plot.
        """
        self.setTitle(f"L{self.plot_region.lane.gel_lane.lane}")

    def _max_bounds(self):
        return [self.min_x, self.max_x]

    @staticmethod
    def _intensities_changed(current_data, new_data):
        return not np.array_equal(current_data[0], new_data[0]) or not np.array_equal(
            current_data[1], new_data[1]
        )
