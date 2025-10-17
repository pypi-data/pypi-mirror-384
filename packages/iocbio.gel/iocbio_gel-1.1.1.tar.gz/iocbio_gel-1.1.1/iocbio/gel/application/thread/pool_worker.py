#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QThreadPool, Slot

from iocbio.gel.application.thread.job import Job
from iocbio.gel.application.thread.worker import Worker


class PoolWorker(Worker):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()
        self._jobs = 0

    @property
    def jobs(self):
        return self._jobs + super().jobs

    def start(self, job: Job) -> None:
        job.state_signals.ready.connect(self.on_exit)
        job.state_signals.error.connect(self.on_exit)
        self._jobs += 1
        self.pool.start(job)
        self.signals.jobs_changed.emit(self.jobs)

    @Slot(str)
    def on_exit(self) -> None:
        self._jobs -= 1
        self.signals.jobs_changed.emit(self.jobs)
