#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from pathlib import Path
from typing import Callable

from PySide6.QtCore import Slot

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image import Image
from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.application.image.repository_backend import ImageRepositoryBackend
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.application.thread.fetch_image_from_omero import FetchImageFromOmero
from iocbio.gel.application.thread.thread_pool import ThreadPool
from iocbio.gel.domain.gel_image import GelImage


class CallbackHelper:
    def __init__(self, omero_id: int, gel_image_id: int, callback: Callable):
        self.omero_id = omero_id
        self.callback = callback
        self.gel_image_id = gel_image_id

    def process(self, omero_id: int, file_location: str):
        if self.omero_id == omero_id:
            self.callback(self.gel_image_id, file_location)
            return True
        return False


class ImageRepositoryBackendOmero(ImageRepositoryBackend):
    def __init__(
        self, omero_client: OmeroClient, thread_pool: ThreadPool, event_registry: EventRegistry
    ):
        self.event_registry = event_registry
        self.omero_client = omero_client
        self.thread_pool = thread_pool
        self.tasks = []

        self.event_registry.omero_image_fetched.connect(self._on_omero_fetched)

    def get_file(self, gel_image: GelImage, image: Image, callback: Callable) -> Image:
        if not gel_image.omero_id:
            image.state = ImageState.MISSING
            return image

        image.name = str(gel_image.omero_id)
        image.file = self.omero_client.get_image_from_cache(gel_image.omero_id)

        if image.file is not None:
            image.file = Path(image.file)
        elif self.omero_client.has_session():
            task = CallbackHelper(gel_image.omero_id, gel_image.id, callback)
            self.tasks.append(task)
            job = FetchImageFromOmero(gel_image.omero_id, self.omero_client)
            job.signals.ready.connect(self.event_registry.omero_image_fetched)
            self.thread_pool.start(job)
        else:
            image.state = ImageState.MISSING
        return image

    @Slot(int, str)
    def _on_omero_fetched(self, omero_id, file_location):
        self.tasks = [task for task in self.tasks if not task.process(omero_id, file_location)]
