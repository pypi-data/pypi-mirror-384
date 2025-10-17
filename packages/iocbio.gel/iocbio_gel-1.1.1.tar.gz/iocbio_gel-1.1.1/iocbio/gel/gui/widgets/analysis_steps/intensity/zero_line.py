#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import pyqtgraph as pg
from PySide6.QtCore import QLineF


class ZeroLine(pg.PolyLineROI):
    """
    Widget allowing the user to manipulate the line which separates intensity background from signal on plot view.
    """

    MARGIN = 1

    def __init__(self, points, is_static=True, bounds=None, *args, **kwargs):
        self.is_static = is_static
        self.bounds = bounds
        super().__init__(
            points,
            rotatable=False,
            resizable=False,
            removable=False,
            movable=False,
            closed=False,
            pen=pg.mkPen({"color": "#666666", "width": 2}),
            hoverPen=pg.mkPen({"color": "#000000", "width": 2}),
            handlePen=pg.mkPen({"color": "#333333", "width": 2}),
            handleHoverPen=pg.mkPen({"color": "#000000", "width": 2}),
            *args,
            **kwargs,
        )

    def checkPointMove(self, handle, pos, modifiers):
        """
        Overwriting parent to keep points in bounds and avoid self intersection.
        This method is called to check if the zero-line handles are allowed to move.
        """
        if self.is_static:
            return False

        if len(self.segments) < 3:
            return True

        moving = []
        fixed = []

        for segment in self.segments:
            h1 = segment.handles[0]["item"]
            h2 = segment.handles[1]["item"]

            line = QLineF(h1.pos(), h2.pos())
            if h1 == handle or h2 == handle:
                moving.append(line)
            else:
                fixed.append(line)

        for moving_segment in moving:
            for fixed_segment in fixed:
                if self._intersects_along_the_segment(moving_segment, fixed_segment):
                    return False

        return True

    def addSegment(self, h1, h2, index=None):
        """
        Overwriting parent to restrict deleting handles.
        """
        super().addSegment(h1, h2, index)

        self.getHandles()[0].setDeletable(False)
        self.getHandles()[-1].setDeletable(False)

        self._toggle_editable_handles()

    def segmentClicked(self, segment, ev=None, pos=None):
        """
        Overwriting parent to restrict splitting segments.
        """
        if self.is_static:
            return

        if ev.double():
            super().segmentClicked(segment, ev, pos)

    def as_points(self):
        """
        Return the zero-line as a list of the point of its handles.
        """
        return [(handle["pos"].x(), handle["pos"].y()) for handle in self.handles]

    def snap_to_bounds(self):
        """
        First and last point should always snap to the sides, rest only when close enough.
        """
        if self.bounds is None:
            return

        handles = self.getHandles()

        if handles[0].pos().x() != self.bounds[0]:
            self.movePoint(
                handles[0],
                self._snap_point(self.bounds[0], handles[0].pos().y()),
                finish=False,
            )

        if handles[-1].pos().x() != self.bounds[1]:
            self.movePoint(
                handles[-1],
                self._snap_point(self.bounds[1], handles[-1].pos().y()),
                finish=False,
            )

        for i in range(len(handles)):
            self._move_if_necessary(handles[i], handles[i].pos().x(), handles[i].pos().y())

    def set_static(self, is_static=True):
        self.is_static = is_static
        self._toggle_editable_handles()

    def _toggle_editable_handles(self):
        handles = self.getHandles()
        for i in range(1, len(handles) - 1):
            handles[i].setDeletable(not self.is_static)

    def _move_if_necessary(self, handle, x1, y1):
        x2, y2 = self._snap_point(x1, y1)
        if x1 == x2 and y1 == y2:
            return

        self.movePoint(handle, (x2, y2), finish=False)

    def _snap_point(self, x, y) -> tuple:
        """
        Box starts at top-left so those are expected to be 0.
        """
        if x - self.MARGIN <= self.bounds[0]:
            x = self.bounds[0]
        if x + self.MARGIN >= self.bounds[1]:
            x = self.bounds[1]
        return x, y

    @staticmethod
    def _intersects_along_the_segment(a: QLineF, b: QLineF):
        """
        Identify if the intersection happens on the segments while also specifically not on the segment end points.
        """
        intersection, point = a.intersects(b)
        if intersection != QLineF.IntersectionType.BoundedIntersection:
            return False

        return not ((a.p1() == point or a.p2() == point) and (b.p1() == point or b.p2() == point))
