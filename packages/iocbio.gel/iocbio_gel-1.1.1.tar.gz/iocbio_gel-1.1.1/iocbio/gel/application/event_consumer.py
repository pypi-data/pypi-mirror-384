#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import SignalInstance


class EventConsumer:
    """
    Decorator for assist unsubscribing from Qt events before object destruction.
    """

    def __init__(self):
        self.events = []
        # has to be lambda as it looks to get disconnected before destroyed
        # is emitted
        self.destroyed.connect(lambda: self.unsubscribe())

    def subscribe(self, event: SignalInstance, callback):
        self.events.append((event, callback))
        event.connect(callback)

    def unsubscribe(self):
        for pair in self.events:
            try:
                pair[0].disconnect(pair[1])
            except Exception:
                # exception "Failed to disconnect ..." is
                # triggered occasionally
                pass
        self.events.clear()
