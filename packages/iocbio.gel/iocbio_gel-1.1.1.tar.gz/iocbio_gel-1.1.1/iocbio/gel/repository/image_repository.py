#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import imageio as iio
import logging
import numpy as np

from copy import copy
from pathlib import Path
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QPixmap, QImage
from qimage2ndarray import raw_view

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.background_method import BackgroundMethod
from iocbio.gel.application.image.image import Image
from iocbio.gel.application.image.image_source import ImageSource
from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.image.processing_cache import ProcessingCache
from iocbio.gel.application.image.region import Region
from iocbio.gel.application.image.repository_backend import ImageRepositoryBackend
from iocbio.gel.application.thread.rolling_ball import RollingBall
from iocbio.gel.application.thread.load_image_preview import LoadImagePreview
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.application.thread.thread_pool import ThreadPool
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.repository.gel_image_repository import GelImageRepository


logger = logging.getLogger(__name__)


class ImageRepository(QObject):
    FLAT_PERCENTILE = 1

    @staticmethod
    def get_original_data(filename):
        """
        Loads image as displayed in most image viewing programs
        and converts it into grayscale 16-bit unsigned int matrix.
        """
        raw = QPixmap(filename).toImage()
        raw = raw.convertToFormat(QImage.Format_Grayscale16)
        raw = raw_view(raw).copy()
        return np.uint16(raw)

    @staticmethod
    def get_raw_data(filename):
        """
        Loads image raw data as it is, ignoring colormaps and image inversions tags.
        For multi-frame images, averages all frames.
        """
        raw = np.array(iio.imread(filename), dtype=np.float64)
        logger.debug(f"imageio loaded, shape: {raw.shape}, ndim: {raw.ndim}")
        if raw.ndim == 3:
            logger.debug(f"Averaging {raw.shape[0]} frames")
            raw = np.mean(raw, axis=0)
            logger.debug(f"Averaged shape: {raw.shape}")
        elif raw.ndim > 3:
            logger.debug("ndim > 3, falling back to get_original_data")
            return np.float64(ImageRepository.get_original_data(filename))

        return raw

    def __init__(
        self,
        gel_image_repository: GelImageRepository,
        event_registry: EventRegistry,
        image_source_setup: ImageSourceSetup,
        image_repository_backend_local: ImageRepositoryBackend,
        image_repository_backend_omero: ImageRepositoryBackend,
        processing_cache: ProcessingCache,
        thread_pool: ThreadPool,
    ):
        super().__init__()
        self.gel_image_repository = gel_image_repository
        self.setup = image_source_setup
        self.event_registry = event_registry
        self.processing_cache = processing_cache
        self.thread_pool = thread_pool
        self.images = {}
        self._backends = {
            ImageSource.LOCAL: image_repository_backend_local,
            ImageSource.OMERO: image_repository_backend_omero,
        }

    def get(self, gel_image: GelImage) -> Image:
        if gel_image.id is None:
            raise RuntimeError("Trying to get gel image without ID assigned to gel_image")

        image = self.images.get(gel_image.id, Image())

        if image.state == ImageState.READY:
            return image

        image = self._fetch(gel_image, image)
        self.images[gel_image.id] = image

        return copy(image)

    def delete(self, image_id: int):
        if image_id in self.images:
            del self.images[image_id]

    def set(self, image_id: int, image: Image):
        self.images[image_id] = copy(image)

    def _fetch(self, gel_image: GelImage, image: Image) -> Image:
        backend: ImageRepositoryBackend = self._backends[self.setup.get_type()]
        image = backend.get_file(gel_image=gel_image, image=image, callback=self._on_async_fetch)

        if image.state == ImageState.MISSING:
            return image

        if image.file is None:
            return image

        if image.preview is None:
            return self._defer_preview_loading(gel_image, image)

        image = self._attach_raw(image)
        image = self._attach_region(gel_image, image)
        return self._attach_background(gel_image, image)

    def _attach_raw(self, image: Image) -> Image:
        image.original = self.get_original_data(image.file)
        image.raw = self.get_raw_data(image.file)
        return image

    def _attach_region(self, gel_image: GelImage, image: Image) -> Image:
        cache_key = ProcessingCache.region_key(gel_image)
        cached = self.processing_cache.get(cache_key)
        if cached is not None:
            image.region = cached
        else:
            result = Region.crop(gel_image, image.raw)
            image.region = result
            self.processing_cache.set(cache_key, result)

        return image

    def _attach_background(self, gel_image: GelImage, image: Image) -> Image:
        if gel_image.background_method == BackgroundMethod.FLAT:
            background_value = np.percentile(image.region, self.FLAT_PERCENTILE)
            image.background = np.full(image.region.shape, background_value)
            image.subtracted = image.region - background_value
            image.state = ImageState.READY
            return image

        if gel_image.background_method == BackgroundMethod.NONE:
            image.state = ImageState.READY
            return image

        cached = self.processing_cache.get(ProcessingCache.background_key(gel_image))
        if cached is not None:
            image.background = cached[0]
            image.subtracted = cached[1]
            image.state = ImageState.READY
            return image

        if self._can_defer_background_job(gel_image):
            return self._defer_bg_subtraction(gel_image, image)

        image.state = ImageState.READY
        return image

    def _defer_preview_loading(self, gel_image: GelImage, image: Image) -> Image:
        self.images[gel_image.id] = image

        job = LoadImagePreview(gel_image.id, image)
        job.signals.ready.connect(self._handle_preview_loading)
        self.thread_pool.start(job)

        return image

    def _defer_bg_subtraction(self, gel_image: GelImage, image: Image) -> Image:
        self.images[gel_image.id] = image

        job = RollingBall(
            gel_image.id,
            image.region,
            gel_image.background_method,
            not gel_image.background_is_dark,
            gel_image.background_radius_x,
            gel_image.background_radius_y,
            gel_image.background_scale,
            ProcessingCache.background_key(gel_image),
        )

        job.signals.ready.connect(self._handle_subtraction_result)
        self.thread_pool.start(job)

        return image

    def _emit_image_ready(self, gel_image: GelImage, image: Image):
        if image.state in [ImageState.MISSING, ImageState.READY]:
            self.event_registry.gel_image_ready.emit(gel_image, image)

    def _on_async_fetch(self, gel_image_id: int, file_location: str):
        gel_image: GelImage = self.gel_image_repository.get(gel_image_id)
        image: Image = self.images.get(gel_image_id)

        if image is None:
            return

        if not file_location:
            image.state = ImageState.MISSING
        else:
            image.file = Path(file_location)
            self.event_registry.set_status_message(f"Loaded image {image.name}")
        self.set(gel_image_id, image)

        image = self.get(gel_image)
        self._emit_image_ready(gel_image, image)

    @Slot(int, Image)
    def _handle_preview_loading(self, gel_image_id: int, image: Image):
        gel_image = self.gel_image_repository.get(gel_image_id)
        self.set(gel_image.id, image)
        image = self.get(gel_image)
        self._emit_image_ready(gel_image, image)

    @Slot(int, np.ndarray, np.ndarray, str)
    def _handle_subtraction_result(self, image_id, background, subtracted, cache_key):
        gel_image = self.gel_image_repository.get(image_id)

        if ProcessingCache.background_key(gel_image) != cache_key:
            self.event_registry.set_status_message("Dropping expired subtraction")
            return

        self.processing_cache.set(
            ProcessingCache.background_key(gel_image), [background, subtracted]
        )

        image = self.images.get(image_id)
        image.background = background
        image.subtracted = subtracted
        image.state = ImageState.READY

        self.set(gel_image, image)
        self._emit_image_ready(gel_image, image)
        self.event_registry.set_status_message(f"Background subtracted for image {image.name}")

    @staticmethod
    def _can_defer_background_job(gel_image):
        return (
            gel_image.background_method == BackgroundMethod.BALL
            and gel_image.background_radius_x is not None
        ) or (
            gel_image.background_method == BackgroundMethod.ELLIPSOID
            and gel_image.background_radius_x is not None
            and gel_image.background_radius_y is not None
        )
