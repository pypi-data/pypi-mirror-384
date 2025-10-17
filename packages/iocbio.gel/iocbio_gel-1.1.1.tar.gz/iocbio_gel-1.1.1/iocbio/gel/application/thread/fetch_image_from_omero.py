#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Signal

from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.application.thread.job import Job


class Signals(QObject):
    ready = Signal(int, str)


class FetchImageFromOmero(Job):
    def __init__(self, omero_id, omero_client: OmeroClient):
        super().__init__(omero_id)
        self.signals = Signals()
        self.omero_id = omero_id
        self.omero_client = omero_client

    def run_job(self) -> None:
        try:
            location = self.omero_client.get_image(self.omero_id, False)
            self.signals.ready.emit(self.omero_id, location)
        except ValueError as e:
            self.signals.ready.emit(self.omero_id, "")
            raise e

    def supersedes(self, job: "Job") -> bool:
        return isinstance(job, self.__class__) and self.omero_id == job.omero_id
