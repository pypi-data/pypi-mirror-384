#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Signal

from iocbio.gel.application.thread.job import Job
from iocbio.gel.application.image.processing_cache import ProcessingCache


class CacheSizeSignals(QObject):
    ready = Signal(object)  # Changed from int to object to handle large sizes


class CalculateCacheSize(Job):
    def __init__(self, processing_cache: ProcessingCache):
        super().__init__("cache-update")
        self.signals = CacheSizeSignals()
        self.processing_cache = processing_cache

    def run_job(self) -> None:
        size = self.processing_cache.get_cache_size()
        self.signals.ready.emit(size)


class ClearCacheSignals(QObject):
    ready = Signal()


class ClearCache(Job):
    def __init__(self, processing_cache: ProcessingCache):
        super().__init__("cache-remove")
        self.signals = ClearCacheSignals()
        self.processing_cache = processing_cache

    def run_job(self) -> None:
        self.processing_cache.clear_cache()
        self.signals.ready.emit()
