#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from collections import deque
from PySide6.QtCore import Slot

from iocbio.gel.application.thread.job import Job
from iocbio.gel.application.thread.pool_worker import PoolWorker


class SequentialWorker(PoolWorker):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue = deque()
        self.current = None

    @property
    def jobs(self):
        return len(self.queue) + super().jobs

    def start(self, job: Job) -> None:
        if self._is_duplicate(job):
            return

        self.queue = deque(filter(lambda x: not job.supersedes(x), self.queue))
        self.queue.append(job)
        self.signals.jobs_changed.emit(self.jobs)

        if self.current is None:
            self._run_next()

    @Slot(str)
    def on_exit(self) -> None:
        super().on_exit()
        self.current = None
        self._run_next()

    def _run_next(self) -> None:
        if len(self.queue) == 0:
            return

        if self.current is not None:
            return

        job = self.queue.popleft()
        self.current = repr(job)
        super().start(job)

    def _is_duplicate(self, job: Job):
        if self.current is not None and self.current == repr(job):
            return True
        for j in self.queue:
            if repr(j) == repr(job):
                return True
        return False
