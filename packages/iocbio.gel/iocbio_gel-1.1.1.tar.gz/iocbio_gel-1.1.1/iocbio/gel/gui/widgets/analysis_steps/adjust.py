#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import pyqtgraph as pg

from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QPalette, QShowEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFormLayout, QPushButton, QMessageBox
from pyqtgraph import ImageItem

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.adjust_roi import AdjustROI
from iocbio.gel.repository.gel_image_repository import GelImageRepository
from iocbio.gel.gui.widgets.viewbox_empty_contextmenu import ViewBoxEmptyContextMenu
from iocbio.gel.gui.widgets.control_slider import ControlSlider
from iocbio.gel.repository.image_repository import ImageRepository
from iocbio.gel.domain.detect_analysis_region import detect_analysis_region


class Adjust(QWidget):
    """
    View for the "Adjust" tab.
    """

    def __init__(
        self,
        gel_image_repository: GelImageRepository,
        image_repository: ImageRepository,
        event_registry: EventRegistry,
        application_state: ApplicationState,
    ):
        super().__init__()

        self.gel_image_repository = gel_image_repository
        self.image_repository = image_repository
        self.event_registry = event_registry
        self.application_state = application_state

        self.gel_image = None
        self.image_raw = None

        self.image = ImageItem()
        self.image.setZValue(-100)

        self.plot = pg.PlotWidget(
            title="Adjust",
            background=self.palette().color(QPalette.AlternateBase).name(),
            viewBox=ViewBoxEmptyContextMenu(),
        )
        self.plot.invertY(True)
        self.plot.setAspectLocked(True)
        self.plot.addItem(self.image)
        self.plot.getPlotItem().hideAxis("bottom")
        self.plot.getPlotItem().hideAxis("left")
        self.plot.hideButtons()
        vb = self.plot.getPlotItem().getViewBox()
        vb.add_view_all_action(self.plot, self.plot)
        vb.add_export_view_action(self.plot, self.plot)

        self.settings = QFormLayout()

        self.apply_button = QPushButton("Apply")
        self.apply_button.setDisabled(True)
        self.apply_button.clicked.connect(self.on_apply)
        self.settings.addRow(self.apply_button)

        self.add_remove_roi_button = QPushButton("")
        self.update_add_remove_button(True)
        self.add_remove_roi_button.setVisible(False)
        self.add_remove_roi_button.clicked.connect(self.on_add_remove)
        self.settings.addRow(self.add_remove_roi_button)

        self.roi_rotation_angle = ControlSlider("Set ROI rotation angle:", 0, -180, 180, 70, 0.01)
        self.roi_rotation_angle.sigValueChanged.connect(self.angle_changed)
        self.settings.addRow(self.roi_rotation_angle)
        self.roi_rotation_angle.setDisabled(True)
        self.roi_rotation_angle.setVisible(False)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.plot, 1)
        self.layout.addLayout(self.settings)

        self.roi: Optional[AdjustROI] = None
        self.roi_pen = pg.mkPen({"color": QColor(255, 0, 0, 255), "width": 2})

        self.setLayout(self.layout)

        self.application_state.mode_changed.connect(self.on_application_state_changed)

    def showEvent(self, event: QShowEvent) -> None:
        """
        Change ROI and image if gel_image in context doesn't match current
        TODO: instead of always recreating ROI - check if update is needed
        """
        super().showEvent(event)
        gel_image: GelImage = self.application_state.context.image

        if self.roi:
            self.plot.removeItem(self.roi)
            self.roi = None

        if not gel_image:
            self.image.clear()
            return

        image = gel_image.image.raw
        if image is None:
            self.image.clear()
            return

        if self.image_raw is not image:
            self.image.setImage(image.T)

        self.gel_image = gel_image
        self.image_raw = image

        if gel_image.region and not self.roi:
            x1, y1, _, _, width, height = gel_image.deserialize_region()
            self.roi = self._create_roi(x1, y1, width, height, gel_image.rotation)
            self.plot.addItem(self.roi)
            self.apply_button.setDisabled(False)
            self.roi_rotation_angle.setDisabled(False)
            self.roi_rotation_angle.set_position(gel_image.rotation)

        self.plot.autoRange(padding=0)

        self.on_application_state_changed(self.application_state.mode)

    def remove_roi(self):
        """
        Propagate update to database when the region selection box is removed.
        """
        self.plot.removeItem(self.roi)
        self.roi = None
        self.gel_image.rotation = 0
        self.gel_image.region = None
        self.gel_image_repository.update(self.gel_image)
        self.roi_rotation_angle.setDisabled(True)
        self.update_add_remove_button(True)
        self.on_apply()

    def roi_changed(self):
        """
        Enable the apply button to visually indicate that a change has happened.
        """
        self.apply_button.setDisabled(False)
        self.roi_rotation_angle.setDisabled(False)
        angle = self.roi.angle()
        self.roi_rotation_angle.set_position(angle - (angle + 180) // 360 * 360)

    def add_roi(self):
        """
        Place a new ROI box on the image if none exists.
        """
        if self.roi or not self.gel_image:
            return

        image = self.gel_image.image.raw
        x1, y1, width, height = detect_analysis_region(image)
        self.roi = self._create_roi(x1, y1, width, height, 0.0)
        self.roi.set_adjustable(self.application_state.mode == ApplicationMode.EDITING)
        self.plot.addItem(self.roi)
        self.apply_button.setDisabled(False)
        self.roi_rotation_angle.setDisabled(False)
        self.roi_rotation_angle.set_position(0.0)
        self.update_add_remove_button(False if self.roi else True)

    def on_apply(self):
        """
        Propagate the ROI box manipulation results to the database.
        """
        if self.gel_image.lanes:
            popup = self._create_confirmation_popup()
            if popup.exec() != QMessageBox.StandardButton.Ok:
                return

        if self.roi is None:
            self.gel_image.rotation = None
            self.gel_image.region = None
        else:
            x1, y1, x2, y2, width, height, angle = self.roi.get_state()
            self.gel_image.rotation = angle
            self.gel_image.region = self.gel_image.serialize_region(x1, y1, x2, y2, width, height)

        self.apply_button.setDisabled(True)
        self.roi_rotation_angle.setDisabled(True)

        image = self.gel_image.image
        image.remove_region()
        self.image_repository.set(self.gel_image.id, image)
        self.gel_image.image = self.image_repository.get(self.gel_image)

        self.gel_image_repository.update(self.gel_image)
        self.event_registry.adjust_applied.emit()

    def update_add_remove_button(self, enable_add: bool):
        if enable_add:
            self.add_remove_roi_button.setText("Add ROI")
        else:
            self.add_remove_roi_button.setText("Remove ROI")

    def on_add_remove(self):
        self.update_add_remove_button(False if self.roi else True)
        if self.roi:
            self.remove_roi()
        else:
            self.add_roi()

    def angle_changed(self, angle):
        if not self.roi:
            return
        self.roi.setAngle(angle, center=[1, 1])

    @Slot(ApplicationMode)
    def on_application_state_changed(self, mode: ApplicationMode):
        """
        Disable ROI box interactions when not in editing mode.
        """
        allow_editing = mode == ApplicationMode.EDITING
        self.apply_button.setDisabled(not allow_editing)

        if self.roi:
            self.roi.set_adjustable(allow_editing)
        else:
            self.roi_rotation_angle.setDisabled(True)

        self.add_remove_roi_button.setVisible(allow_editing)
        self.update_add_remove_button(False if self.roi else True)
        self.roi_rotation_angle.setVisible(allow_editing)

    def _create_roi(self, x, y, width, height, angle):
        """
        Create the box which allows the user to select and rotate a region on the image.
        """
        roi = AdjustROI(
            view_box=self.plot.getPlotItem().getViewBox(),
            pos=[x, y],
            size=(width, height),
            angle=angle,
            pen=self.roi_pen,
            movable=True,
            rotatable=True,
            resizable=True,
            removable=True,
            invertible=True,
            scaleSnap=True,
            translateSnap=True,
        )
        roi.addRotateHandle([0, 0], [1, 1])
        roi.sigRemoveRequested.connect(self.remove_roi)
        roi.sigRegionChanged.connect(self.roi_changed)
        return roi

    @staticmethod
    def _create_confirmation_popup():
        box = QMessageBox()
        box.setWindowTitle("Apply ROI changes")
        box.setText(
            "This image already has lanes connected to it. "
            "Changing the selected region will delete them. "
            "Are you sure you want to continue?"
        )
        box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        box.setIcon(QMessageBox.Question)
        return box
