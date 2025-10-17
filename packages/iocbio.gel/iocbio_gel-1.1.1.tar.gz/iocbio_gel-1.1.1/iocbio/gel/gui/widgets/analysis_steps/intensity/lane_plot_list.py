#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.intensity_plot import IntensityPlot
from iocbio.gel.gui.widgets.analysis_steps.intensity.plot_list import PlotList
from iocbio.gel.repository.gel_image_lane_repository import GelImageLaneRepository


class LanePlotList(PlotList):
    """
    Scrollable list holding the individual intensity plots in the "Lanes" tab.
    """

    def __init__(
        self,
        event_registry: EventRegistry,
        application_state: ApplicationState,
        plot_provider: Callable[..., IntensityPlot],
        repository: GelImageLaneRepository,
    ):
        super().__init__(event_registry, application_state)
        self.plot_provider = plot_provider
        self.repository = repository

    def create_plot(self, region: PlotRegion):
        """
        Create a plot which monitors the zero-line changes.
        """
        return self.plot_provider(
            plot_region=region,
            min_y=self.plot.min_h,
            max_y=self.plot.max_h,
            on_change_callback=self.on_zero_line_change,
        )

    def on_zero_line_change(self, plot_region: PlotRegion):
        """
        Propagate widget changes to database.
        """
        plot_region.lane.set_zero_line(plot_region.points)
        self.repository.update(plot_region.lane)
