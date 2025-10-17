#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging

from PySide6.QtCore import QObject, Slot

from iocbio.gel.application.thread.fetch_image_from_omero import FetchImageFromOmero
from iocbio.gel.application.thread.job import Job
from iocbio.gel.application.thread.pool_worker import PoolWorker
from iocbio.gel.application.thread.sequential_worker import SequentialWorker
from iocbio.gel.application.thread.rolling_ball import RollingBall
from iocbio.gel.application.thread.load_image_preview import LoadImagePreview
from iocbio.gel.application.thread.worker import Worker
from iocbio.gel.application.event_registry import EventRegistry


class ThreadPool(QObject):
    def __init__(self, event_registry: EventRegistry):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.event_registry = event_registry

        self.workers: dict[str, Worker] = {
            RollingBall.__name__: SequentialWorker(),
            FetchImageFromOmero.__name__: SequentialWorker(),
            LoadImagePreview.__name__: SequentialWorker(),
            "default": PoolWorker(),
        }

        for w in self.workers.values():
            w.signals.jobs_changed.connect(self.on_jobs_changed)

    def start(self, job: Job) -> None:
        job.state_signals.start.connect(self.on_start)
        job.state_signals.ready.connect(self.on_ready)
        job.state_signals.error.connect(self.on_error)

        worker = self.workers.get(job.__class__.__name__, self.workers["default"])
        worker.start(job)

    @Slot(int)
    def on_jobs_changed(self):
        jobs = sum([w.jobs for w in self.workers.values()])
        self.event_registry.status_jobs.emit(jobs)

    @Slot(str)
    def on_start(self, key: str):
        self.logger.debug("Starting job %s", key)

    @Slot(str)
    def on_ready(self, key: str):
        self.logger.debug("Finished job %s", key)

    @Slot(str, Exception)
    def on_error(self, key: str, exception: Exception):
        self.logger.error(
            "Job %s encountered an error: %s", key, exception, stack_info=True, exc_info=True
        )
