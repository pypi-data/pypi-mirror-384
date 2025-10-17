#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import orm
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.base import NO_VALUE

from iocbio.gel.db.entity_visitor import EntityVisitor


class Base(object):
    """
    Base class for database entities.
    """

    def __init__(self):
        self.saved_state = {}

    @orm.reconstructor
    def init_on_load(self):
        """
        Initializer for SQLAlchemy.
        """
        self.saved_state = {}
        self.mark_state_saved()

    def mark_state_saved(self):
        """
        Mark the current state of the object as saved to the database.
        """
        if not hasattr(self, "saved_state"):
            self.saved_state = {}
        for key in self.__table__.columns.keys():
            self.saved_state[key] = getattr(self, key)

    def get_saved_state(self):
        """
        Get the state of the properties from last database save point.
        """
        if not hasattr(self, "saved_state"):
            self.saved_state = {}
            return
        state = {}
        dirty_keys = self._sa_instance_state.committed_state.keys()
        for key in dirty_keys:
            state[key] = None if self.saved_state[key] == NO_VALUE else self.saved_state[key]
        return state

    def get_dirty_state(self):
        """
        Get the changed properties.
        """
        modified_state = {}
        dirty_keys = self._sa_instance_state.committed_state.keys()
        for key in dirty_keys:
            modified_state[key] = getattr(self, key)
        return modified_state

    def get_current_state(self):
        state = {}
        for key in self.__table__.columns.keys():
            state[key] = getattr(self, key)
        return state

    def restore_state(self, state):
        """
        Overwrite entity attributes with the given state values.
        """
        for key, value in state.items():
            setattr(self, key, value)

    def accept(self, visitor: EntityVisitor):
        visitor.visit(self)


Entity = declarative_base(cls=Base)
