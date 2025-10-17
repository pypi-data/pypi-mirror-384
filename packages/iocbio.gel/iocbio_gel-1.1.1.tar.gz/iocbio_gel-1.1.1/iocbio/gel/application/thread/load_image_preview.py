#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QImage, QPixmap
from copy import copy

import iocbio.gel.gui.style as style

from iocbio.gel.application.thread.job import Job
from iocbio.gel.application.image.image import Image


class Signals(QObject):
    ready = Signal(int, Image)


class LoadImagePreview(Job):
    def __init__(self, gel_image_id: int, image: Image):
        super().__init__(gel_image_id, image.file)
        self.signals = Signals()
        self.gel_image_id = gel_image_id
        self.image = copy(image)
        if self.image.file is None:
            raise RuntimeError(f"Trying to load pixmap for an image without file {self.image.name}")

    def run_job(self) -> None:
        try:
            size = style.PREVIEW_ICON_SIZE.width()
            qimage = QImage(self.image.file).scaled(size, size, Qt.KeepAspectRatioByExpanding)
            h, w = qimage.height(), qimage.width()

            self.image.preview = QPixmap.fromImage(
                qimage.copy(
                    (w - size) // 2,
                    (h - size) // 2,
                    size,
                    size,
                )
            )
            self.signals.ready.emit(self.gel_image_id, self.image)
        except ValueError as e:
            self.signals.ready.emit(self.gel_image_id, None)
            raise e

    def supersedes(self, job: "Job") -> bool:
        return isinstance(job, self.__class__) and self.gel_image_id == job.gel_image_id
