#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from PySide6.QtCore import QLineF

from iocbio.gel.domain.gel_image_lane import GelImageLane


class PlotRegion:
    """
    A user-selected region on the pixel intensity plot of a lane.
    Holds the integration bounds and zero-line points placed by the user.
    """

    def __init__(self, lane: GelImageLane):
        self.intensities = lane.calculate_intensities()
        self.points = lane.get_zero_line()
        d = np.append(self.intensities, np.array(self.points)[:, 1])
        self.min_intensity = np.min(d)
        self.max_intensity = np.max(d)
        self.lane = lane
        self.lane_id = lane.id
        self.min_limit, self.max_limit = lane.get_region_range()

    def _make_limit_lines(self):
        a = np.max(self.points) + 10
        b = np.min(self.points) - 10
        return QLineF(self.min_limit, a, self.min_limit, b), QLineF(
            self.max_limit, a, self.max_limit, b
        )

    def _get_points_in_limit(self, x1, y1, x2, y2, min_line, max_line) -> list:
        """
        For a given segment return points that are either within the bounds or on the bound intersections.
        """
        line = QLineF(x1, y1, x2, y2)
        min_point = self._get_bounded_intersection_point(min_line, line)
        max_point = self._get_bounded_intersection_point(max_line, line)

        if min_point and max_point:
            return [(min_point.x(), min_point.y()), (max_point.x(), max_point.y())]
        if min_point:
            return [(min_point.x(), min_point.y()), (x2, y2)]
        if max_point:
            return [(x1, y1), (max_point.x(), max_point.y())]

        points = []
        if self.min_limit < x1 < self.max_limit:
            points.append((x1, y1))
        if self.min_limit < x2 < self.max_limit:
            points.append((x2, y2))
        return points

    @staticmethod
    def _right_trapezoid_area(x1, y1, x2, y2):
        return (y1 + y2) * (abs(x1 - x2) / 2)

    @staticmethod
    def _get_bounded_intersection_point(a: QLineF, b: QLineF):
        intersection, point = a.intersects(b)
        if intersection == QLineF.IntersectionType.BoundedIntersection:
            return point
        return None
