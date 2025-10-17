#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Signal, SignalInstance

from iocbio.gel.application.image.image import Image
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.domain.project import Project


class EventRegistry(QObject):
    """
    Keeping event signals in one place to track usage.
    """

    adjust_applied: SignalInstance = Signal()
    history_changed: SignalInstance = Signal(int, int)
    gel_added: SignalInstance = Signal(Gel)
    gel_deleted: SignalInstance = Signal(int)
    gel_updated: SignalInstance = Signal(Gel)
    gel_selected: SignalInstance = Signal(Gel)
    gel_lane_added: SignalInstance = Signal(GelLane)
    gel_lane_deleted: SignalInstance = Signal(int)
    gel_lane_updated: SignalInstance = Signal(GelLane)
    gel_lane_selected: SignalInstance = Signal(GelLane)
    gel_image_lane_added: SignalInstance = Signal(GelImageLane)
    gel_image_lane_deleted: SignalInstance = Signal(int)
    gel_image_lane_updated: SignalInstance = Signal(GelImageLane)
    gel_image_lane_selected: SignalInstance = Signal(GelImageLane)
    gel_image_added: SignalInstance = Signal(GelImage)
    gel_image_deleted: SignalInstance = Signal(int)
    gel_image_updated: SignalInstance = Signal(GelImage)
    gel_image_selected: SignalInstance = Signal(GelImage)
    gel_image_ready: SignalInstance = Signal(GelImage, Image)
    gel_image_roi_changed: SignalInstance = Signal(GelImage)
    measurement_added: SignalInstance = Signal(Measurement)
    measurement_updated: SignalInstance = Signal(Measurement)
    measurement_deleted: SignalInstance = Signal(int)
    measurement_selected: SignalInstance = Signal(Measurement)
    measurement_type_added: SignalInstance = Signal(MeasurementType)
    measurement_type_updated: SignalInstance = Signal(MeasurementType)
    measurement_type_deleted: SignalInstance = Signal(int)
    measurement_changed_plots: SignalInstance = Signal(Measurement)
    measurement_lane_added: SignalInstance = Signal(MeasurementLane)
    measurement_lane_updated: SignalInstance = Signal(MeasurementLane)
    measurement_lane_deleted: SignalInstance = Signal(int)
    measurement_lane_selected: SignalInstance = Signal(MeasurementLane)
    omero_image_fetched: SignalInstance = Signal(int, str)
    project_added: SignalInstance = Signal(Project)
    project_deleted: SignalInstance = Signal(int)
    project_updated: SignalInstance = Signal(Project)
    project_selected: SignalInstance = Signal(Project)
    added_gel_to_project: SignalInstance = Signal(object, object)
    removed_gel_from_project: SignalInstance = Signal(object, object)
    db_connected: SignalInstance = Signal()
    colormap_changed: SignalInstance = Signal()
    status_message: SignalInstance = Signal(str, bool)
    status_jobs: SignalInstance = Signal(int)

    def __init__(self):
        super().__init__()

    def set_status_message(self, message: str, is_prolonged: bool = False):
        self.status_message.emit(message, is_prolonged)
