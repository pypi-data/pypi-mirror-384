#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Signal

from iocbio.gel.application.thread.job import Job


class Signals(QObject):
    jobs_changed = Signal(int)


class Worker(QObject):
    def __init__(self, *key: str):
        super().__init__()
        self.signals = Signals()

    @property
    def jobs(self):
        return 0

    def start(self, job: Job) -> None:
        raise NotImplementedError
