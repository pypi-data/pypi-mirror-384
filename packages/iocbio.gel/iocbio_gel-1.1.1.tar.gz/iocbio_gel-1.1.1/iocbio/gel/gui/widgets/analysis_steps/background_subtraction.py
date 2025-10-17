#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Dict, Union, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot, Qt, QRectF, Signal
from PySide6.QtGui import QPalette, QColor, QShowEvent
from PySide6.QtWidgets import (
    QWidget,
    QGraphicsPixmapItem,
    QHBoxLayout,
    QGroupBox,
    QVBoxLayout,
    QPushButton,
)
from pyqtgraph import (
    GradientEditorItem,
    ImageItem,
    HistogramLUTWidget,
    mkColor,
    HistogramLUTItem,
)

from iocbio.gel.application.application_state.context import Context, Analysis
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image import Image
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.background.bg_color_box import BgColorBox
from iocbio.gel.gui.widgets.analysis_steps.background.bg_subtraction_box import BgSubtractionBox
from iocbio.gel.repository.gel_image_repository import GelImageRepository
from iocbio.gel.gui.widgets.viewbox_empty_contextmenu import ViewBoxEmptyContextMenu
from iocbio.gel.repository.image_repository import ImageRepository


class CurrentViewBox(ViewBoxEmptyContextMenu):
    sigWheel = Signal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def wheelEvent(self, ev):
        s = 1.01 ** (ev.delta() * self.state["wheelScaleFactor"])
        self.sigWheel.emit(s)


class BackgroundSubtraction(QWidget):
    """
    View for the "Background" tab.
    """

    SETTINGS_HISTOGRAM_STATE_KEY = "gel_image/histogram_widget_state"

    APPLY_LABEL = {
        ImageState.READY: "Apply",
        ImageState.LOADING: "Applying ...",
    }

    def __init__(
        self,
        event_registry: EventRegistry,
        gel_image_repository: GelImageRepository,
        image_repository: ImageRepository,
        settings: SettingsProxy,
        application_state: ApplicationState,
    ):
        super().__init__()

        self.event_registry = event_registry
        self.gel_image_repository = gel_image_repository
        self.image_repository = image_repository
        self.settings = settings
        self.application_state = application_state

        self.gel_image: Optional[GelImage] = None
        self.image_region = None
        self.image_bg = None
        self.image_subtracted = None

        self.layout = QHBoxLayout()

        color = self.palette().color(QPalette.AlternateBase).name()
        self.img_plots: Dict[str, Dict[str, Union[pg.PlotWidget, QGraphicsPixmapItem]]] = {
            "raw": {
                "plot": pg.PlotWidget(
                    title="Raw", background=color, viewBox=ViewBoxEmptyContextMenu()
                ),
                "img": ImageItem(),
            },
            "bg": {
                "plot": pg.PlotWidget(
                    title="Background", background=color, viewBox=ViewBoxEmptyContextMenu()
                ),
                "img": ImageItem(),
            },
            "result": {
                "plot": pg.PlotWidget(
                    title="Result", background=color, viewBox=ViewBoxEmptyContextMenu()
                ),
                "img": ImageItem(),
            },
            "zoom_overview": {
                "plot": pg.PlotWidget(
                    title="Current view", background=color, viewBox=CurrentViewBox()
                ),
                "img": ImageItem(),
            },
        }

        self.plot_view_range = self.img_plots["raw"]["plot"].getViewBox().viewRange()

        self.settings_layout = QVBoxLayout()

        self.color_group = BgColorBox("Background Color")
        self.settings_layout.addWidget(self.color_group)

        self.subtract_group = BgSubtractionBox("Background Subtraction")
        self.settings_layout.addWidget(self.subtract_group)

        self.apply_button = QPushButton(self.APPLY_LABEL[ImageState.READY])
        self.apply_button.clicked.connect(self.save_background_change)
        self.settings_layout.addWidget(self.apply_button)

        zoom_overview_layout = QVBoxLayout()
        zoom_overview = self.img_plots["zoom_overview"]["plot"]
        self.zoom_box = pg.RectROI(
            [0, 0],
            size=[0, 0],
            angle=0,
            pen=pg.mkPen({"color": QColor(255, 0, 0, 255), "width": 2}),
            movable=True,
            maxBounds=QRectF(0, 0, 0, 0),
            rotatable=False,
            resizable=False,
            removable=False,
            invertible=False,
            scaleSnap=False,
            translateSnap=False,
        )
        self.zoom_box.removeHandle(0)
        self.zoom_box.sigRegionChanged.connect(self.on_zoom_box_moved)
        self.img_plots["zoom_overview"]["plot"].getViewBox().sigWheel.connect(
            self.on_zoom_box_zoomed
        )
        zoom_overview.addItem(self.zoom_box)
        zoom_overview.setMouseEnabled(x=False)
        zoom_overview.setMouseEnabled(y=False)
        zoom_overview.setMaximumSize(250, 200)
        zoom_overview_layout.addWidget(zoom_overview, alignment=Qt.AlignHCenter)

        view_all_button = QPushButton("View all")
        view_all_button.clicked.connect(self.auto_range)
        zoom_overview_layout.addWidget(view_all_button)
        self.settings_layout.addLayout(zoom_overview_layout, Qt.AlignVCenter)

        histogram_group = QGroupBox("Colormap")
        self.histogram_layout = QVBoxLayout()

        self.histogram_widget = HistogramLUTWidget(
            orientation="horizontal", background=mkColor(0, 0, 0, 0)
        )
        self.colormap_color_count: Optional[int] = None
        self.histogram_widget.item.gradient.loadPreset("grey")
        self.histogram_widget.item.sigLevelChangeFinished.connect(
            self.on_histogram_level_change_finished
        )
        self.histogram_widget.item.gradient.sigGradientChangeFinished.connect(
            self.on_gradient_change_finished
        )

        self.histogram_layout.addWidget(self.histogram_widget)
        histogram_group.setLayout(self.histogram_layout)
        histogram_group.setMinimumWidth(300)
        self.settings_layout.addStretch()
        self.settings_layout.addWidget(histogram_group)

        for key, val in self.img_plots.items():
            self._add_plot(key, val["plot"], val["img"])

        self.layout.addLayout(self.settings_layout)

        self.setLayout(self.layout)

        self.img_plots["raw"]["plot"].getViewBox().sigResized.connect(
            lambda: self.set_view_range(self.plot_view_range)
        )

        self.application_state.context_changed.connect(self.on_context_change)
        self.application_state.mode_changed.connect(self.on_application_state_changed)
        self.event_registry.gel_image_updated.connect(self.on_image_changed)
        self.event_registry.colormap_changed.connect(self.on_colormap_changed)

        self.on_application_state_changed(self.application_state.mode)

    def set_view_range(self, view_range: list, tol=1e-12, block_set_zoom_box_pos=False):
        for key, value in self.img_plots.items():
            if key == "zoom_overview":
                continue

            plot = value["plot"]
            plot.sigRangeChanged.disconnect(self.on_view_range_changed)

            vr = view_range
            nr = plot.viewRange()

            if block_set_zoom_box_pos:
                plot.setRange(xRange=vr[0], yRange=vr[1], padding=0)
            else:
                if abs(vr[0][0] - nr[0][0]) > tol or abs(vr[0][1] - nr[0][1]) > tol:
                    plot.setYRange(vr[1][0], vr[1][1], padding=0)

                if abs(vr[1][0] - nr[1][0] > tol) or abs(vr[1][1] - nr[1][1]) > tol:
                    plot.setXRange(vr[0][0], vr[0][1], padding=0)

            plot.sigRangeChanged.connect(self.on_view_range_changed)

        self.plot_view_range = self.img_plots["raw"]["plot"].viewRange()
        if not block_set_zoom_box_pos:
            self.set_zoom_box_pos()

    def on_view_range_changed(self, plot: pg.PlotWidget):
        view_range = plot.viewRange()
        self.set_view_range(view_range)

    def set_zoom_box_pos(self, pos=None):
        if pos is None:
            [x0, x1], [y0, y1] = self.plot_view_range
        else:
            [x0, x1], [y0, y1] = pos
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        w = self.img_plots["zoom_overview"]["img"].width() or x0
        h = self.img_plots["zoom_overview"]["img"].height() or y0
        x1 = min(w, x1)
        y1 = min(h, y1)
        self.zoom_box.setSize((max(x1 - x0, 0), max(y1 - y0, 0)))
        self.zoom_box.setPos((min(x0, w), min(y0, h)))

    def on_zoom_box_moved(self):
        pos = self.zoom_box.pos()
        size = self.zoom_box.size()
        view_range = [[pos.x(), pos.x() + size.x()], [pos.y(), pos.y() + size.y()]]
        self.set_view_range(view_range, block_set_zoom_box_pos=True)

    def on_zoom_box_zoomed(self, scale: float):
        pos = self.zoom_box.pos()
        size = self.zoom_box.size()
        center = pos + 0.5 * size
        nsize = 0.5 * scale * size
        new_position = [
            [center.x() - nsize.x(), center.x() + nsize.x()],
            [center.y() - nsize.y(), center.y() + nsize.y()],
        ]
        self.set_zoom_box_pos(new_position)

    def auto_range(self):
        for k in ["raw", "bg", "result"]:
            if self.img_plots[k]["img"].image is None:
                continue
            self.img_plots[k]["plot"].autoRange(padding=0)

    def on_histogram_level_change_finished(self, histogram: HistogramLUTItem):
        """
        Save histogram object data to settings, used in subsequent views.
        """
        new_state = histogram.saveState()
        current_state = self.settings.get(self.SETTINGS_HISTOGRAM_STATE_KEY)

        if new_state == current_state:
            return

        self.settings.set(self.SETTINGS_HISTOGRAM_STATE_KEY, new_state)

        self.event_registry.colormap_changed.emit()

    def on_gradient_change_finished(self, _: GradientEditorItem):
        """
        Save histogram object data to settings, used in subsequent views.
        """
        new_state = self.histogram_widget.item.saveState()
        current_state = self.settings.get(self.SETTINGS_HISTOGRAM_STATE_KEY)

        if new_state == current_state:
            return

        self.settings.set(self.SETTINGS_HISTOGRAM_STATE_KEY, new_state)

        self.event_registry.colormap_changed.emit()

    @Slot()
    def on_colormap_changed(self):
        """
        Apply previously saved histogram settings.
        """
        histogram_state: Optional[Dict[str, any]] = self.settings.get(
            self.SETTINGS_HISTOGRAM_STATE_KEY
        )
        if not histogram_state:
            histogram_state = self.histogram_widget.item.saveState()

        level_min, level_max = histogram_state["levels"]

        histogram_state["levels"] = (level_min, level_max)

        self.histogram_widget.item.restoreState(histogram_state)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.on_image_changed(self.application_state.context.image)

    @Slot(GelImage)
    def on_image_changed(self, gel_image: GelImage) -> None:
        """
        Rebuild the visuals if the gel image has changed.
        """
        if self.application_state.context.image != gel_image:
            return

        if not gel_image or gel_image.image.final is None:
            for key in self.img_plots:
                self.img_plots[key]["img"].clear()
            self.gel_image = None
            return

        image = self.image_repository.get(gel_image)
        if self.gel_image == gel_image and self._image_is_same(image):
            return

        self.gel_image = gel_image
        self.image_region = image.region
        self.image_bg = image.background
        self.image_subtracted = image.subtracted

        self.color_group.set_dark(self.gel_image.background_is_dark)
        self.subtract_group.load_from_image(self.gel_image)

        self._set_image(image)

    def save_background_change(self):
        self.subtract_group.load_to_image(self.gel_image)
        self.gel_image.background_is_dark = self.color_group.is_dark()

        image = self.gel_image.image
        image.remove_background()
        self.image_repository.set(self.gel_image.id, image)
        self.gel_image.image = self.image_repository.get(self.gel_image)

        self.apply_button.setText(self.APPLY_LABEL[image.state])
        self.apply_button.setDisabled(True)

        self.gel_image_repository.update(self.gel_image)

    @Slot(Context)
    def on_context_change(self, context: Context):
        if not isinstance(context, Analysis):
            self.on_image_changed(None)

    @Slot(ApplicationMode)
    def on_application_state_changed(self, mode: ApplicationMode):
        """
        Disable ROI box interactions when not in editing mode.
        """
        is_disabled = mode != ApplicationMode.EDITING
        self.apply_button.setDisabled(is_disabled)
        self.color_group.setDisabled(is_disabled)
        self.subtract_group.setDisabled(is_disabled)

    def _set_image(self, image: Image):
        self.apply_button.setText(self.APPLY_LABEL[image.state])
        self.apply_button.setDisabled(image.state != ImageState.READY or self._editing_disabled())

        self.img_plots["raw"]["img"].setImage(image.region.T)

        if image.background is None:
            self.img_plots["bg"]["img"].clear()
        else:
            self.img_plots["bg"]["img"].setImage(image.background.T)

        if image.subtracted is None:
            self.img_plots["result"]["img"].clear()
        else:
            self.img_plots["result"]["img"].setImage(image.subtracted.T)

        self._set_colormap(image)

        zoom_overview_img = self.img_plots["zoom_overview"]["img"]
        zoom_overview_img.setImage(image.region.T)
        self.zoom_box.maxBounds = QRectF(
            0, 0, zoom_overview_img.width(), zoom_overview_img.height()
        )

        self.auto_range()

        self.plot_view_range = self.img_plots["raw"]["plot"].getViewBox().viewRange()

    def _add_plot(self, key: str, plot: pg.PlotWidget, img: QGraphicsPixmapItem):
        plot.invertY(True)
        plot.addItem(img)
        plot.setAspectLocked(True)
        plot.getPlotItem().hideAxis("bottom")
        plot.getPlotItem().hideAxis("left")
        plot.hideButtons()

        if key == "zoom_overview":
            return

        plot.sigRangeChanged.connect(self.on_view_range_changed)

        vb = plot.getPlotItem().getViewBox()
        vb.add_view_all_action(self, plot, action=self.auto_range)
        vb.add_export_view_action(self, plot)

        self.layout.addWidget(plot)

    def _editing_disabled(self):
        return self.application_state.mode != ApplicationMode.EDITING

    def _set_colormap(self, image: Image):
        plot, data = (
            ("raw", image.region) if image.subtracted is None else ("result", image.subtracted)
        )

        self.colormap_color_count = np.max(data)
        self.on_colormap_changed()
        self.histogram_widget.item.setImageItem(self.img_plots[plot]["img"])

    def _image_is_same(self, image: Image):
        return (
            self.image_region is image.region
            and self.image_bg is image.background
            and self.image_subtracted is image.subtracted
        )
