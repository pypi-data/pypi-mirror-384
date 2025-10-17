#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Dict, Union

import pyqtgraph as pg
from pyqtgraph import ImageItem
from PySide6.QtGui import QPalette, QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QGraphicsPixmapItem

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.viewbox_empty_contextmenu import ViewBoxEmptyContextMenu


class Raw(QWidget):
    """
    Display the original image in "Raw" tab.
    """

    def __init__(self, application_state: ApplicationState):
        super().__init__()

        self.application_state = application_state
        self.image_raw = None
        self.image_original = None

        color = self.palette().color(QPalette.AlternateBase).name()
        self.img_plots: Dict[str, Dict[str, Union[str, pg.PlotWidget, QGraphicsPixmapItem]]] = {
            "original": {
                "plot": pg.PlotWidget(
                    title="Original", background=color, viewBox=ViewBoxEmptyContextMenu()
                ),
                "img": ImageItem(),
            },
            "raw": {
                "plot": pg.PlotWidget(
                    title="Raw", background=color, viewBox=ViewBoxEmptyContextMenu()
                ),
                "img": ImageItem(),
            },
        }

        self.layout = QHBoxLayout()
        for val in self.img_plots.values():
            self._add_plot(val["plot"], val["img"])

        self.setLayout(self.layout)

    def showEvent(self, event: QShowEvent) -> None:
        """
        Show image currently in context.
        """
        super().showEvent(event)
        gel_image: GelImage = self.application_state.context.image

        if not self._valid_image(gel_image):
            self.img_plots["raw"]["img"].clear()
            self.img_plots["original"]["img"].clear()
            return

        raw = gel_image.image.raw
        original = gel_image.image.original

        if self.image_raw is raw and self.image_original is original:
            return

        self.image_raw = raw
        self.image_original = original

        self.img_plots["raw"]["img"].setImage(raw.T)
        self.img_plots["original"]["img"].setImage(original.T)

        for key in self.img_plots:
            self.img_plots[key]["plot"].autoRange(padding=0)

    def _add_plot(self, plot: pg.PlotWidget, img: QGraphicsPixmapItem):
        plot.invertY(True)
        plot.addItem(img)
        plot.setAspectLocked(True)
        plot.getPlotItem().hideAxis("bottom")
        plot.getPlotItem().hideAxis("left")
        plot.hideButtons()
        plot.setMouseEnabled(x=False)
        plot.setMouseEnabled(y=False)

        self.layout.addWidget(plot)

        vb = plot.getPlotItem().getViewBox()
        vb.add_view_all_action(self, plot)
        vb.add_export_view_action(self, plot)

    @staticmethod
    def _valid_image(gel_image: GelImage) -> bool:
        return (
            gel_image
            and gel_image.hash
            and gel_image.image.raw is not None
            and gel_image.image.original is not None
        )
