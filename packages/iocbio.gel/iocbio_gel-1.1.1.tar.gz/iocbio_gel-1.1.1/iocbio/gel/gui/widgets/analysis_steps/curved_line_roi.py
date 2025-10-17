#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
import copy

from typing import Callable

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPainterPath
from pyqtgraph import ROI, mkPen, mkBrush, TextItem, Point, ImageItem

from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.curved_lane_region import CurvedLaneRegion as LaneRegion


class CurvedLineRoi(ROI):
    LINE_SNAP_DISTANCE = 5
    WIDTH_HANDLE_NAME = "width_handle"

    def __init__(
        self,
        lane_region: LaneRegion,
        gel_image_lane: GelImageLane,
        image: ImageItem,
        measurement_id: int,
        gel_image_lane_updated_callback: Callable[[GelImageLane], None],
        gel_image_lane_removed_callback: Callable[[GelImageLane], None],
        lane_selected_callback: Callable[[GelImageLane], None],
        changes_allowed: bool = True,
        paint_integral_range: bool = False,
        *args,
        **kwargs,
    ):
        self.lane_region = lane_region
        self.path_resolution = 1

        self.edge_pen = mkPen({"color": "#4E8F38", "width": 2, "dash": [3, 4]})
        self.edge_line_pen = copy.copy(self.edge_pen)
        self.edge_hover_pen = mkPen({"color": "#FF0000", "width": 2, "dash": [3, 4]})
        self.integral_range_pen = mkPen({"color": "#fc8403", "width": 3})
        self.paint_integral_range = paint_integral_range

        self.roi_center_path = None
        self.roi_bounding_box = None
        self._bad_handle = None

        self.gel_image_lane = gel_image_lane
        self.measurement_id = measurement_id
        self.image_width, self.image_height = image.width(), image.height()

        self.gel_image_lane_updated_callback = gel_image_lane_updated_callback
        self.gel_image_lane_removed_callback = gel_image_lane_removed_callback
        self.lane_selected_callback = lane_selected_callback
        self.changes_allowed = changes_allowed

        spl = self.lane_region.spline
        self.draw_path()
        bounding_rect = self.boundingRect()

        self.maxBounds = QRectF(0, 0, 1.2 * self.image_width, self.image_height)

        self.label = TextItem(
            "" if self.gel_image_lane.gel_lane is None else f"L{self.gel_image_lane.gel_lane.lane}",
            color=(0, 0, 0),
            anchor=(0.5, 1),
            fill=(255, 255, 255, 200),
        )

        ROI.__init__(
            self,
            pos=[bounding_rect.x(), bounding_rect.y()],
            size=[1, 1],
            maxBounds=self.maxBounds,
            removable=self.changes_allowed,
            *args,
            **kwargs,
        )
        self.setPos(bounding_rect.x(), bounding_rect.y())

        self.setAcceptedMouseButtons(Qt.LeftButton)

        if not self.changes_allowed:
            self.translatable = False

        for i, p in enumerate(lane_region.nodes):
            h = self.addFreeHandle([p[0] - bounding_rect.x(), p[1] - bounding_rect.y()])
            h.name = None
            if 0 < i < len(lane_region.nodes) - 1:
                h.setDeletable(True)
                h.sigRemoveRequested.connect(self._on_remove_handle)
                h.show() if self.translatable else h.hide()

        width_handle_pos = Point(
            spl(bounding_rect.y() + 0.5 * bounding_rect.height())
            - bounding_rect.x()
            + self.lane_region.width / 2,
            0.5 * bounding_rect.height(),
        )

        self.width_handle = self.addFreeHandle(
            width_handle_pos, (0.5, 0.5), name=self.WIDTH_HANDLE_NAME
        )
        self.width_handle.name = self.WIDTH_HANDLE_NAME
        self.width_handle.show() if self.translatable else self.width_handle.hide()

        self.set_roi_nodes()
        self.draw_path()
        self.generate_bounding_box()

        self.label.setParentItem(self)
        self.label.setPos(
            self.mapFromParent(self.pos().x() + self.handles[0]["item"].pos().x(), self.pos().y())
        )

        self.sigRegionChanged.connect(self._on_region_changed)
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)
        self.sigRemoveRequested.connect(self._on_region_remove)
        self.sigClicked.connect(self._on_region_selected)

        self.update()

    def set_roi_nodes(self):
        x = np.array([self.handles[i]["item"].pos().x() for i in range(len(self.handles) - 1)])
        y = np.array([self.handles[i]["item"].pos().y() for i in range(len(self.handles) - 1)])
        self.lane_region.nodes = x, y

    def draw_path(self):
        spl = self.lane_region.spline
        _, _y = self.lane_region.nodes_xy

        # Creating y-coordinates so that the drawn path will go thru handle midpoints
        y = np.array([_y[0]])
        for i in range(len(_y) - 1):
            segment = np.arange(
                max(0, np.ceil(_y[i])),
                min(np.floor(_y[i + 1]), self.image_height),
                self.path_resolution,
            )
            if segment.size < 2:
                continue

            y = np.concatenate([y, segment, [_y[i + 1]]])

        x = spl(y)

        self.roi_center_path = QPainterPath()
        self.roi_center_path.moveTo(x[0], y[0])
        for i in range(1, y.size):
            self.roi_center_path.lineTo(x[i], y[i])

        return self.roi_center_path

    def generate_bounding_box(self):
        path = self.draw_path() if self.roi_center_path is None else self.roi_center_path
        rect = path.boundingRect()
        self.roi_bounding_box = QRectF(
            rect.x() - self.lane_region.width / 2,
            rect.y(),
            rect.width() + self.lane_region.width,
            rect.height(),
        )
        return self.roi_bounding_box

    def boundingRect(self):
        return (
            self.generate_bounding_box() if self.roi_bounding_box is None else self.roi_bounding_box
        )

    def update(self):
        super().update()
        ml = None
        for _ml in self.gel_image_lane.measurement_lanes:
            if _ml.measurement_id == self.measurement_id:
                ml = _ml
                break

        if ml is None or self.paint_integral_range is False:
            self.label.fill = mkBrush((255, 255, 255, 200))
        else:
            self.label.fill = mkBrush((255, 230, 0, 200))
        self.label.update()

    def draw_integral_range(self, p: QPainter):
        ml = None
        for _ml in self.gel_image_lane.measurement_lanes:
            if _ml.measurement_id == self.measurement_id:
                ml = _ml
                break

        if ml is None or self.paint_integral_range is False:
            return

        spl = self.lane_region.spline
        _, _y = self.lane_region.nodes_xy
        pos_y = self.pos().y()

        mn = ml.min or 0
        mx = ml.max or self.image_height
        mn = max(mn - pos_y, _y[0])
        mx = min(mx - pos_y, _y[-1])

        y = np.arange(mn, mx + 1)
        if y.size < 1:
            return
        x = spl(y)

        integral_path = QPainterPath()
        integral_path.moveTo(x[0], y[0])
        for i in range(1, y.size):
            integral_path.lineTo(x[i], y[i])

        p.setPen(self.integral_range_pen)
        half_width = self.lane_region.width / 2
        p.drawPath(integral_path.translated(half_width, 0))
        p.drawPath(integral_path.translated(-half_width, 0))

    def paint(self, p: QPainter, opt, widget):
        if self._bad_handle is not None:
            self._check_for_bad_handle()
            return

        half_width = self.lane_region.width / 2
        path = self.draw_path() if self.roi_center_path is None else self.roi_center_path

        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(self.currentPen) if self.translatable else p.setPen(self.pen)
        p.drawPath(path)

        self.draw_integral_range(p)

        p.setPen(self.edge_pen)
        p.drawPath(path.translated(half_width, 0))
        p.drawPath(path.translated(-half_width, 0))

    def mouseDragEvent(self, ev):
        """
        Prevent modifications when not in editing mode.
        """
        if not self.changes_allowed:
            return
        mods = ev.modifiers() & ~self.mouseDragHandler.snapModifier
        if mods == self.mouseDragHandler.translateModifier:
            super().mouseDragEvent(ev)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()

        if ev.button() == Qt.MouseButton.RightButton and self.contextMenuEnabled():
            self.raiseContextMenu(ev)
            ev.accept()
        elif ev.double():
            if not self.changes_allowed:
                ev.ignore()
                return

            ev_pos_y = ev.pos().y()

            spl = self.lane_region.spline

            x_on_line = spl(ev_pos_y)
            x_dist_from_line = (
                self.mapToDevice(Point(x_on_line, ev_pos_y)) - self.mapToDevice(ev.pos())
            ).x()

            if abs(x_dist_from_line) > self.LINE_SNAP_DISTANCE:
                ev.ignore()
                return

            index = None
            for i in range(len(self.handles)):
                if ev_pos_y < self.handles[i]["item"].pos().y():
                    index = i
                    break

            h = self.addFreeHandle((x_on_line, ev_pos_y), index=index)
            h.name = None
            h.setDeletable(True)
            h.sigRemoveRequested.connect(self._on_remove_handle)
            ev.accept()
        elif self.acceptedMouseButtons() & ev.button():
            ev.accept()
            self.sigClicked.emit(self, ev)
        else:
            ev.ignore()

    def checkPointMove(self, handle, pos, modifiers):
        if not self.changes_allowed:
            return False

        if handle.name == self.WIDTH_HANDLE_NAME:
            spl = self.lane_region.spline
            hpos = handle.pos()
            bounding_rect = self.boundingRect()

            if hpos.y() < 0 + bounding_rect.y():
                self._bad_handle = handle, Point(hpos.x(), 0 + bounding_rect.y())
                return False

            if hpos.y() > bounding_rect.height():
                self._bad_handle = handle, Point(hpos.x(), bounding_rect.height())
                return False

            width = hpos.x() - spl(hpos.y())
            if width < 1:
                self.lane_region.width = 2
                self._bad_handle = handle, Point(
                    spl(hpos.y()) + self.lane_region.width / 2, hpos.y()
                )
                return False
            else:
                self.lane_region.width = 2 * width
                return True

        else:
            self._set_width_handle_position()
            if not self._check_spline_handler_move(handle):
                return False

            return True

    def _makePen(self):
        # Generate the pen color for this ROI based on its current state.
        if self.mouseHovering:
            self.edge_pen = self.edge_hover_pen
            return self.hoverPen
        else:
            self.edge_pen = self.edge_line_pen
            return self.pen

    def _check_for_bad_handle(self):
        if self._bad_handle is not None:
            handle, pos = self._bad_handle
            handle.setPos(pos)
            handle.movePoint(self.mapToScene(pos))
            self._bad_handle = None

    def _set_width_handle_position(self, y=None):
        spl = self.lane_region.spline
        _, _y = self.lane_region.nodes_xy
        hpos = self.width_handle.pos()
        y = min(max(hpos.y(), _y[0]), min(hpos.y(), _y[-1]))
        wpos = Point(spl(hpos.y()) + self.lane_region.width / 2, y)

        self.width_handle.setPos(wpos)
        self.sigRegionChangeFinished.disconnect(self._on_region_change_finished)
        self.width_handle.movePoint(self.mapToScene(wpos))
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)

    def _check_spline_handler_move(self, handle):
        index = self.indexOfHandle(handle)
        # the last place in self.handler list is reserved for the width handler
        last_index = len(self.handles) - 2

        point_offset = 1.0e-3
        if index == 0:
            lower_y_bound = 0.0 - self.pos().y()
            point_offset = 0.0
        else:
            lower_y_bound = self.handles[index - 1]["item"].pos().y()

        if index == last_index:
            upper_y_bound = self.image_height - self.pos().y()
            point_offset = 0.0
        else:
            upper_y_bound = self.handles[index + 1]["item"].pos().y()

        x = handle.pos().x()
        y = handle.pos().y()

        if lower_y_bound > y:
            pos = Point(x, lower_y_bound + point_offset)
            self._bad_handle = handle, pos
            return False

        if upper_y_bound < y:
            pos = Point(x, upper_y_bound - point_offset)
            self._bad_handle = handle, pos
            return False

        half_width = self.lane_region.width / 2

        if handle.pos().x() + self.pos().x() + half_width > self.image_width:
            pos = Point(handle.pos().x() + 0 * half_width, handle.pos().y())
            self._bad_handle = handle, pos
            return False

        if handle.pos().x() + self.pos().x() - half_width < 0:
            pos = Point(handle.pos().x() + 0 * half_width, handle.pos().y())
            self._bad_handle = handle, pos
            return False

        return True

    def _on_region_changed(self, region: ROI):
        self.set_roi_nodes()
        self.draw_path()
        self.generate_bounding_box()

        bounding_rect = self.boundingRect()

        self.maxBounds = QRectF(
            0 - bounding_rect.x(),
            0 - bounding_rect.y(),
            self.image_width - bounding_rect.width() + 1,
            self.image_height - bounding_rect.height() + 1,
        )
        pos_x, pos_y = region.pos().x(), region.pos().y()

        self.label.setPos(
            self.mapFromParent(pos_x + self.handles[0]["item"].pos().x(), pos_y + bounding_rect.y())
        )

    def _is_region_correct(self):  # noqa: C901
        if self._bad_handle is not None:
            return False

        no_handles = len(self.handles) - 1

        if self.pos().y() + self.handles[no_handles - 1]["item"].pos().y() > self.image_height:
            h = self.handles[no_handles - 1]["item"]
            hpos = Point(h.pos().x(), self.image_height - self.pos().y())
            self._bad_handle = h, hpos
            return False

        if self.pos().y() + self.handles[0]["item"].pos().y() < 0:
            h = self.handles[0]["item"]
            hpos = Point(h.pos().x(), 0)
            self._bad_handle = h, hpos
            return False

        _, _y = self.lane_region.nodes_xy
        offset = 1e-3
        bad_index = None
        len_y_1 = len(_y) - 1
        for i in range(len_y_1):
            if _y[i] >= _y[i + 1]:
                bad_index = i
                break

        if _y[-1] < _y[-2]:
            bad_index = len_y_1
        if bad_index is not None:
            if bad_index == 0:
                h = self.handles[bad_index]["item"]
                hpos = Point(h.pos().x(), self.handles[bad_index + 1]["item"].pos().y() - offset)
                self._bad_handle = h, hpos
                return False

            if bad_index == len_y_1:
                h = self.handles[bad_index]["item"]
                hpos = Point(h.pos().x(), self.handles[bad_index - 1]["item"].pos().y() + offset)
                self._bad_handle = h, hpos
                return False

            d1 = _y[bad_index] - _y[bad_index - 1]
            d2 = _y[bad_index + 1] - _y[bad_index]

            if abs(d1) < abs(d2):
                h = self.handles[bad_index]["item"]
                hpos = Point(h.pos().x(), self.handles[bad_index - 1]["item"].pos().y() + offset)
                self._bad_handle = h, hpos
            else:
                h = self.handles[bad_index]["item"]
                hpos = Point(h.pos().x(), self.handles[bad_index + 1]["item"].pos().y() - offset)
                self._bad_handle = h, hpos
            return False

        return True

    def _on_region_change_finished(self, region: ROI):
        if not self.gel_image_lane:
            return

        if not self._is_region_correct():
            return

        self.lane_region.offset(self.pos().x(), self.pos().y())
        self.gel_image_lane.set_region(self.lane_region)

        if self.gel_image_lane_updated_callback:
            self.gel_image_lane_updated_callback(self.gel_image_lane)

    def _on_remove_handle(self, handle):
        if not self.changes_allowed:
            return
        super().removeHandle(handle)
        self._on_region_changed(self)
        self._set_width_handle_position()
        self.lane_region.offset(self.pos().x(), self.pos().y())
        self.gel_image_lane.set_region(self.lane_region)
        if self.gel_image_lane_updated_callback:
            self.gel_image_lane_updated_callback(self.gel_image_lane)

    def _on_region_selected(self, region: ROI):
        if self.lane_selected_callback and self.gel_image_lane:
            self.lane_selected_callback(self.gel_image_lane)
        self.update()

    def _on_region_remove(self, region: ROI):
        if not self.changes_allowed:
            return
        if self.gel_image_lane_removed_callback and self.gel_image_lane:
            self.sigRegionChanged.disconnect(self._on_region_changed)
            self.sigRegionChangeFinished.disconnect(self._on_region_change_finished)
            self.sigRemoveRequested.disconnect(self._on_region_remove)
            self.sigClicked.disconnect(self._on_region_selected)
            self.gel_image_lane_removed_callback(self)
