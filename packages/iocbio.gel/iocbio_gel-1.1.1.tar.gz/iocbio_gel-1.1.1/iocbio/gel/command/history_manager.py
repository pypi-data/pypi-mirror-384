#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging

from PySide6.QtCore import Slot

from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.command import Command
from iocbio.gel.command.command_set import CommandSet


class HistoryManager:
    """
    Keeps track and performs actions on the undo/redo steps.
    Calling execute/undo on the command while it is still in stack to retain it in history in case of an exception.
    """

    def __init__(self, event_registry: EventRegistry, application_state: ApplicationState):
        self.event_registry = event_registry
        self.logger = logging.getLogger(__name__)
        self.stack = []
        self.reverse = []

        application_state.mode_changed.connect(self.on_change_to_view)
        application_state.context_changed.connect(self.clear)

    def execute(self, command: Command):
        """
        Initial entrypoint for adding a command to history.
        """
        if isinstance(command, CommandSet) and len(command.commands) == 1:
            command = command.commands[0]

        if not command.should_execute:
            return

        callbacks = command.execute()

        self.stack.append(command)
        self._debug(command, ">")
        self.reverse.clear()

        [f() for f in callbacks]
        self._emit_change()

    def undo(self):
        if not self.stack:
            return

        callbacks = self.stack[-1].undo()

        command = self.stack.pop()
        self.reverse.append(command)
        self._debug(command, "<")

        [f() for f in callbacks]
        self._emit_change()

    def redo(self):
        if not self.reverse:
            return

        callbacks = self.reverse[-1].execute()

        command = self.reverse.pop()
        self.stack.append(command)
        self._debug(command, ">")

        [f() for f in callbacks]
        self._emit_change()

    def clear(self):
        """
        Clear history stack and notify the need for solidifying soft deletes.
        """
        if not self.stack and not self.reverse:
            return
        self.stack.clear()
        self.reverse.clear()
        self._emit_change()

    @Slot(ApplicationMode)
    def on_change_to_view(self, mode: ApplicationMode):
        """
        Clear history stack when the application views change to avoid "unseen" modifications.
        """
        if mode == ApplicationMode.VIEWING:
            self.clear()

    def _emit_change(self):
        """
        Notify UI components.
        """
        self.event_registry.history_changed.emit(len(self.stack), len(self.reverse))

    def _debug(self, command: Command, direction: str):
        self.logger.debug(f"{command} {direction} [{len(self.stack)}|{len(self.reverse)}]")
