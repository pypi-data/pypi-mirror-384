#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional, List

from PySide6.QtCore import Qt, Slot, QMargins
from PySide6.QtGui import QShowEvent, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget, QScrollArea, QFrame

from iocbio.gel.application.application_state.context import Context, Analysis
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.plot import Plot
from iocbio.gel.domain.plot_region import PlotRegion
from iocbio.gel.gui.widgets.analysis_steps.intensity.intensity_plot import IntensityPlot


class LayoutWithFixedRatio(QVBoxLayout):
    """
    Helper layout keeping the plot aspect ratio
    """

    def __init__(self, max_height: int = 100):
        super().__init__()
        self._max_height: int = max_height

    @property
    def max_height(self):
        return self._max_height

    @max_height.setter
    def max_height(self, value):
        self._max_height = value
        self.invalidate()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        h = max(200, min(self.max_height, int(w / 1.6)))
        return h


class SelectableFrame(QFrame):
    """
    Helper class showing a selection frame around plots
    """

    def __init__(self, child, parent):
        super().__init__(parent)

        layout = LayoutWithFixedRatio()
        layout.addWidget(child)
        self.setLayout(layout)
        self.layout = layout
        self.child = child
        self.select(False)
        self.set_max_height(parent.height())

    def is_selected(self) -> bool:
        return self.child.isEnabled()

    def select(self, select=True):
        if select:
            self.setFrameStyle(QFrame.StyledPanel)
            self.child.setEnabled(True)
        else:
            self.setFrameStyle(QFrame.Plain)
            self.child.setEnabled(False)

    def leaveEvent(self, event):
        if self.is_selected():
            self.select(False)
        return super().leaveEvent(event)

    def set_max_height(self, height: int):
        margins: QMargins = self.contentsMargins()
        self.layout.max_height = height - (margins.top() + margins.bottom())


class PlotList(QScrollArea):
    """
    Base class for a scrollable list holding the plots.
    """

    def __init__(self, event_registry: EventRegistry, application_state: ApplicationState):
        super().__init__()

        self.application_state = application_state
        self.event_registry = event_registry

        self.gel_image: Optional[GelImage] = None
        self.image_final = None
        self.image_dark = False
        self.plot: Optional[Plot] = None

        widget = QWidget()
        self._layout = QVBoxLayout(widget)
        self._layout.setAlignment(Qt.AlignTop)
        self.setWidget(widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setMinimumWidth(300)

        self._mousePressPos = None

        self.event_registry.gel_image_updated.connect(self.on_image_changed)
        self.event_registry.gel_image_lane_added.connect(self.on_image_lane_updated)
        self.event_registry.gel_image_lane_updated.connect(self.on_image_lane_updated)
        self.event_registry.gel_image_lane_deleted.connect(self.on_image_lane_deleted)
        self.application_state.context_changed.connect(self.on_context_change)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.on_image_changed(self.application_state.context.image)

    def resizeEvent(self, event: QResizeEvent) -> None:
        for i in range(self._layout.count()):
            frame: SelectableFrame = self._layout.itemAt(i).widget()
            frame.set_max_height(event.size().height())
        return super().resizeEvent(event)

    @Slot(GelImage)
    def on_image_changed(self, gel_image: GelImage) -> None:
        """
        Update plots when the current gel image is changed.
        """
        if self.application_state.context.image != gel_image:
            return

        if self._image_is_invalid(gel_image):
            return self.clear()

        if self._image_is_unchanged(gel_image):
            return

        self.gel_image = gel_image
        self.image_dark = gel_image.background_is_dark
        self.image_final = gel_image.image.final

        self.update_plots()

    @Slot(Context)
    def on_context_change(self, context: Context):
        if not isinstance(context, Analysis):
            self.on_image_changed(None)

    @Slot(int)
    def on_image_lane_deleted(self, image_lane_id: int):
        if self._image_is_invalid(self.gel_image):
            return

        for i in range(self._layout.count()):
            if self._layout.itemAt(i).widget().child.plot_region.lane_id == image_lane_id:
                self.update_plots()
                return

    @Slot(GelImageLane)
    def on_image_lane_updated(self, image_lane: GelImageLane):
        """
        Update plots when the current gel image lane is changed.
        """
        if self._image_is_invalid(self.gel_image):
            return

        if self.gel_image.id != image_lane.image_id:
            return

        self.update_plots()

    def update_plots(self):
        """
        Change the underlying data model for plot widgets.
        Create or dispose widgets if their count differs from data regions.
        """

        if self.gel_image.image.state != ImageState.READY:
            self.widget().setHidden(True)
            return

        self.widget().setHidden(False)

        image = self.gel_image.get_plot_data()
        self.plot = Plot(image)

        regions = self.get_plot_regions(image)
        if not regions:
            return self.clear_plots()

        self.plot.regions.extend(regions)
        self.plot.update_limits()

        existing_count = self._layout.count()

        for i, region in enumerate(regions):
            if i < existing_count:
                frame: SelectableFrame = self._layout.itemAt(i).widget()
                plot: IntensityPlot = frame.child
                old_lane_id = plot.plot_region.lane_id
                plot.set_model(region, self.plot.min_h, self.plot.max_h)
                plot.update_title()
                if frame.is_selected() and region.lane_id != old_lane_id:
                    frame.select(False)
            else:
                plot = self.create_plot(region)
                frame = SelectableFrame(plot, self)
                self._layout.addWidget(frame)
                plot.update_title()

        if len(regions) < existing_count:
            for i in reversed(range(len(regions), existing_count)):
                item = self._layout.takeAt(i)
                item.widget().deleteLater()

    def create_plot(self, region: PlotRegion) -> IntensityPlot:
        """
        To be implemented by children.
        """
        pass

    def get_plot_regions(self, image) -> List[PlotRegion]:
        """
        Create plot region objects for active gel image lanes.
        """
        lanes = sorted(self.gel_image.lanes, key=lambda x: x.gel_lane.lane)
        return list(map(lambda x: PlotRegion(x), lanes))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._mousePressPos = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if (
            self._mousePressPos is not None
            and event.button() == Qt.LeftButton
            and self.rect().contains(event.x(), event.y())
        ):
            shift = self.verticalScrollBar().value()
            for i in range(self._layout.count()):
                rect = self._layout.itemAt(i).geometry()
                rect.translate(0, -shift)
                click_inside = rect.contains(event.x(), event.y()) and rect.contains(
                    self._mousePressPos.x(), self._mousePressPos.y()
                )
                frame = self._layout.itemAt(i).widget()
                if click_inside and not frame.is_selected():
                    frame.select(True)

        self._mousePressPos = None

    def clear_plots(self):
        for i in reversed(range(self._layout.count())):
            item = self._layout.takeAt(i)
            item.widget().deleteLater()

    def clear(self):
        self.clear_plots()
        self._replace_image(None)
        self.plot = None

    def _replace_image(self, gel_image):
        self.gel_image = gel_image

    def _image_is_unchanged(self, gel_image: GelImage):
        return (
            self.gel_image == gel_image
            and self.image_dark == gel_image.background_is_dark
            and self.image_final is gel_image.image.final
        )

    @staticmethod
    def _image_is_invalid(gel_image: GelImage) -> bool:
        return gel_image is None or gel_image.image.final is None
