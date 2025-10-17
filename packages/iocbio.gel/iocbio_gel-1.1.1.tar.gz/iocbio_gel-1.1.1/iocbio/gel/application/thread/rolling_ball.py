#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np

from PySide6.QtCore import QObject, Signal, QThreadPool, SignalInstance
from skimage import util, restoration
from skimage.transform import rescale, resize

from iocbio.gel.application.image.background_method import BackgroundMethod
from iocbio.gel.application.thread.job import Job


class Signals(QObject):
    ready: SignalInstance = Signal(int, np.ndarray, np.ndarray, str)


class RollingBall(Job):
    METHODS = [BackgroundMethod.BALL, BackgroundMethod.ELLIPSOID]

    def __init__(
        self,
        image_id,
        source_image,
        method,
        is_light,
        radius_x,
        radius_y,
        should_scale,
        cache_key: str,
    ):
        super().__init__(
            image_id, method, radius_x, radius_y, is_light, str(should_scale), cache_key
        )
        if method not in self.METHODS:
            raise ValueError(f'Unexpected method="{method}" provided for {self.__class__.__name__}')

        self.signals = Signals()
        self.image_id = image_id
        self.source_image = source_image
        self.method = method
        self.is_light = is_light
        self.radius_x = radius_x
        self.radius_y = radius_y if radius_y else radius_x
        self.should_scale = should_scale
        self.cache_key = cache_key

    def run_job(self) -> None:
        pool = QThreadPool.globalInstance()
        thread_count = max(round(pool.maxThreadCount() - pool.activeThreadCount() / 2), 1)
        scale_factor = 1 if not self.should_scale else self._get_scale_factor()

        background, result = self._subtract_background(
            self.source_image,
            self.method,
            self.is_light,
            self.radius_x,
            self.radius_y,
            scale_factor=scale_factor,
            thread_count=thread_count,
        )

        self.signals.ready.emit(self.image_id, background, result, self.cache_key)

    def supersedes(self, job: "Job") -> bool:
        return isinstance(job, self.__class__) and self.image_id == job.image_id

    def _get_scale_factor(self) -> int:
        radius = max(self.radius_x, self.radius_y)
        thresholds = [10, 30, 100, 400, 1200]

        for i, r in enumerate(thresholds):
            if radius <= r:
                return 2**i

        return 2 ** len(thresholds)

    @staticmethod
    def _subtract_background(
        source_image, method, is_light, radius_x, radius_y, scale_factor=1, thread_count=1
    ):
        """
        Rolling ball background subtraction implementation following the example from:
        https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_rolling_ball.html
        """
        radius = radius_x
        kernel = None

        if method == BackgroundMethod.ELLIPSOID:
            kernel = restoration.ellipsoid_kernel((radius_y * 2, radius_x * 2), radius_y + radius_x)

        if is_light:
            source_image_inverted = util.invert(source_image)
            bg_inverted = RollingBall._run_ball(
                source_image_inverted, radius, kernel, scale_factor, thread_count
            )
            result = util.invert(source_image_inverted - bg_inverted)
            bg = util.invert(bg_inverted)
        else:
            bg = RollingBall._run_ball(source_image, radius, kernel, scale_factor, thread_count)
            result = source_image - bg

        return bg, result

    @staticmethod
    def _run_ball(
        image: np.ndarray, radius, kernel, scale_factor: int, thread_count: int
    ) -> np.ndarray:
        if scale_factor <= 1:
            return restoration.rolling_ball(
                image, radius=radius, kernel=kernel, num_threads=thread_count
            )

        small_image = rescale(image, 1 / scale_factor, anti_aliasing=True)

        bg = restoration.rolling_ball(
            small_image, radius=radius, kernel=kernel, num_threads=thread_count
        )

        return resize(bg, image.shape, anti_aliasing=True)
