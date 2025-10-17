#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from functools import reduce
from PySide6.QtCore import QObject, Signal, QRunnable, Qt


class Signals(QObject):
    start = Signal(str)
    ready = Signal(str)
    error = Signal(str, Exception)

    _finished = Signal()
    _instances = dict()

    def __new__(cls):
        instance = super().__new__(cls)
        Signals._instances[id(instance)] = instance
        return instance

    def __init__(self):
        super().__init__()
        self._finished.connect(self.on_finished, Qt.QueuedConnection)

    def on_finished(self):
        instance_id = id(self)
        if instance_id in Signals._instances:
            del Signals._instances[instance_id]


class Job(QRunnable):
    def __init__(self, *key: str):
        super().__init__()
        self.state_signals = Signals()
        self.key = "{}[{}]".format(
            self.__class__.__name__, str(reduce(lambda a, b: str(a) + "/" + str(b), key))
        )

    def __repr__(self):
        return self.key

    def run(self) -> None:
        self.state_signals.start.emit(self.key)
        try:
            self.run_job()
            self.state_signals.ready.emit(self.key)
        except Exception as e:
            self.state_signals.error.emit(self.key, e)
        finally:
            self.state_signals._finished.emit()

    def run_job(self) -> None:
        raise NotImplementedError

    def supersedes(self, job: "Job") -> bool:
        return False
