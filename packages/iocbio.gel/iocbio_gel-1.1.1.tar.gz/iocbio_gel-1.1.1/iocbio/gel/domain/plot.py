#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np

from typing import List

from iocbio.gel.domain.plot_region import PlotRegion


class Plot:
    """
    Wrapper for a collection of intensity plots for placed lanes.
    """

    def __init__(self, image):
        self.regions: List[PlotRegion] = []
        self.image_min = image.min()
        self.image_max = image.max()
        self.min_h, self.max_h = self.image_min, self.image_max

    def update_limits(self):
        """
        Calculates selected region limits.
        """
        if not self.regions:
            self.min_h = self.image_min
            self.max_h = self.image_max
            return
        mn = [region.min_intensity for region in self.regions] + [self.image_min]
        mx = [region.max_intensity for region in self.regions] + [self.image_max]

        self.min_h = np.ceil(np.min(mn))
        self.max_h = np.floor(np.max(mx))
