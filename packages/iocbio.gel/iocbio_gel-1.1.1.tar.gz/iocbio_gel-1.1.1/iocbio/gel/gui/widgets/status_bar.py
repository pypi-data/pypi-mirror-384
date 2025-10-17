#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QStatusBar, QLabel

from iocbio.gel.application.event_registry import EventRegistry


class StatusBar(QStatusBar):
    """
    Application status bar
    """

    MESSAGE_TIMEOUT = {True: 15000, False: 3000}

    def __init__(
        self,
        event_registry: EventRegistry,
    ):
        super().__init__()

        self.jobs_indicator = QLabel()
        self.addPermanentWidget(self.jobs_indicator)

        self._show_message("Ready")
        self._update_jobs()

        # Connect signals
        event_registry.db_connected.connect(lambda: self._show_message("Database connected"))
        event_registry.status_message.connect(self._show_message)
        event_registry.status_jobs.connect(self._update_jobs)

    def _show_message(self, message, is_prolonged=False):
        self.showMessage(message, self.MESSAGE_TIMEOUT[is_prolonged])

    def _update_jobs(self, jobs: int = 0):
        text = f"Jobs: {jobs}" if jobs > 0 else "Idle"
        self.jobs_indicator.setText(text)
