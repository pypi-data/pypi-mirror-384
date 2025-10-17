#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from scipy.signal import convolve


def detect_analysis_region(image):
    is_dark = np.median(image) < np.mean(image)
    image = image - image.min() if is_dark else image.max() - image

    def get_axis_coordinates(axis):
        ax = image.mean(axis=axis)
        k_size = max(int(0.05 * image.shape[1 - axis]), 10)
        kernel = np.blackman(k_size)
        kernel /= kernel.sum()
        smooth = convolve(ax, kernel, mode="same")
        thr = np.median(ax)
        n = int(1.5 * k_size)
        coordinates = np.where(smooth[n:-n] > thr)[0] + n

        upper_limit = ax.size
        if coordinates.size < 2:
            return 0, upper_limit

        padding = max(int(0.01 * image.shape[1 - axis]), 10)
        ax_0, ax_1 = coordinates[0] - padding, coordinates[-1] + padding

        if ax_1 > upper_limit:
            ax_1 = upper_limit

        if ax_1 - ax_0 < 0.1 * upper_limit:
            ax_0, ax_1 = 0, upper_limit

        return ax_0, ax_1

    x0, x1 = get_axis_coordinates(axis=0)
    y0, y1 = get_axis_coordinates(axis=1)
    return x0, y0, x1 - x0, y1 - y0
