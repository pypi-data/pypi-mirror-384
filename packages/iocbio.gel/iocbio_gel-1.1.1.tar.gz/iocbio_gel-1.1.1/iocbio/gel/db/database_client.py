#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging
from typing import Optional

from sqlalchemy import engine_from_config, event
from sqlalchemy.orm import sessionmaker, SessionTransaction, Session
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

import sqlalchemy.exc as exc

from iocbio.gel.db.database_setup import DatabaseSetup


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    """
    Explicitly enable foreign keys for SQLite connection since this is not done default.
    :ref:`Example from https://stackoverflow.com/questions/2614984/sqlite-sqlalchemy-how-to-enforce-foreign-keys#answer-
    15542046`
    """
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


class DatabaseClient:
    """
    Wrapper around SQLAlchemy database session.
    """

    def __init__(self, db_setup: DatabaseSetup) -> None:
        self.logger = logging.getLogger(__name__)
        self.session: Optional[Session] = None
        self.ignore_handles = []
        self.setup = db_setup

    def start_session(self):
        """
        Create a database engine and session.
        To enable query logging, set db.echo=True.
        """
        self.close()
        config = {"db.url": self.setup.get_connection_string(), "db.echo": "False"}
        engine = engine_from_config(config, prefix="db.")
        self.session = sessionmaker(bind=engine, autoflush=False)()

    def get(self, *args):
        return self.session.get(*args)

    def add(self, *args):
        self.session.add(*args)

    def delete(self, *args):
        self.session.delete(*args)

    def start_transaction(self) -> SessionTransaction:
        return self.session.begin_nested()

    def commit(self):
        if self.session.in_nested_transaction():
            return

        try:
            self.session.commit()
        except exc.StatementError as error:
            self.logger.error(
                "Exception occurred while committing a change: %s. Details: %s.",
                error,
                error.detail,
            )
            self.session.rollback()
            raise error
        except exc.SQLAlchemyError as error:
            self.logger.error("Exception occurred while committing a change: %s.", error)
            self.session.rollback()
            raise error

    def execute(self, statement):
        """
        Execute statements

        Execute SQL statements prepared by SQLAlchemy `select`, `delete` or similar
        calls. For requesting scalars, postprocess result by calling `.scalars()`
        """
        return self.session.execute(statement)

    def close(self):
        if self.session:
            self.session.close()
            self.session = None
