#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import SignalInstance

from iocbio.gel.command.command import Command
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.domain.project import Project


class UpdateProject(Command):
    """
    Update project together with its descendants.
    """

    def __init__(self, entity: Project, db: DatabaseClient, update_event: SignalInstance):
        self.db = db
        self.entity = entity
        self.update_event = update_event
        self.before = entity.get_saved_state()
        self.after = entity.get_dirty_state()

    def __repr__(self):
        return f"{self.__class__.__name__}[{self.entity.__class__.__name__}={self.entity.id}]"

    def execute(self):
        self.entity.restore_state(self.after)
        self.db.commit()
        self.entity.mark_state_saved()
        return self._get_callbacks()

    def undo(self):
        self.entity.restore_state(self.before)
        self.db.commit()
        self.entity.mark_state_saved()
        return self._get_callbacks()

    def _get_callbacks(self):
        return [lambda: self.update_event.emit(self.entity)] + [
            lambda: self.update_event.emit(x) for x in self.entity.descendants
        ]
