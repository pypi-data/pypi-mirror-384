#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
import pyqtgraph as pg


class Region:
    @staticmethod
    def crop(gel_image, source_image):
        if not gel_image.region:
            return np.float32(source_image)

        x1, y1, x2, y2, width, height = gel_image.deserialize_region()
        roi = pg.ROI([y1, x1], size=(height, width))
        roi.rotate(-gel_image.rotation or 0)

        cropped_image = roi.getArrayRegion(source_image, pg.ImageItem(image=source_image))
        return np.float32(cropped_image)
