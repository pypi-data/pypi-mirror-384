#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np

from pathlib import Path
from typing import Optional
from PySide6.QtGui import QPixmap

from iocbio.gel.application.image.image_state import ImageState


class Image(object):
    def __init__(
        self,
        name: str = "",
        file: Path = None,
        original: np.ndarray = None,
        raw: np.ndarray = None,
        region: np.ndarray = None,
        background: np.ndarray = None,
        subtracted: np.ndarray = None,
        state: ImageState = ImageState.LOADING,
    ):
        self.name = name
        self.file = file
        self.original = original
        self.raw = raw
        self.region = region
        self.background = background
        self.subtracted = subtracted
        self.preview: QPixmap = None
        self.state = state

    @property
    def final(self) -> Optional[np.ndarray]:
        for result in [self.subtracted, self.region, self.raw]:
            if result is not None:
                return result
        return None

    def remove_region(self):
        self.region = None
        self.remove_background()

    def remove_background(self):
        self.subtracted = None
        self.background = None
        self.state = ImageState.LOADING
