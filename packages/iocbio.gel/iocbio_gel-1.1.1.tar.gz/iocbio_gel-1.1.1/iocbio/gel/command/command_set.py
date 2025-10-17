#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import List, Callable, Iterable

from iocbio.gel.command.command import Command


class CommandSet(Command):
    """
    For running a set of commands as a single history entry.
    """

    def __init__(self, commands: List[Command]):
        """
        Unwrap nested CommandSets.
        """
        self.commands = []

        for command in commands:
            if isinstance(command, CommandSet):
                self.commands.extend(command.commands)
            else:
                self.commands.append(command)

    @property
    def should_execute(self) -> bool:
        return len(self.commands) > 0

    def execute(self) -> list[Callable]:
        return self._execute(self.commands, "execute")

    def undo(self) -> list[Callable]:
        return self._execute(reversed(self.commands), "undo")

    def _execute(self, commands: Iterable[Command], method: str) -> list[Callable]:
        callbacks = []
        for command in commands:
            callbacks.extend(getattr(command, method)())
        return callbacks
