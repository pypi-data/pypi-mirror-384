#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from enum import Enum

from iocbio.gel.db.connection_parameters.connection_parameters import ConnectionParameters
from iocbio.gel.db.connection_parameters.postgresql_parameters import PostgreSQLParameters
from iocbio.gel.db.connection_parameters.sqlite_parameters import SQLiteParameters


class DatabaseType(Enum):
    """
    Currently implemented options.
    """

    POSTGRESQL = ("PostgreSQL", PostgreSQLParameters)
    SQLITE = ("SQLite", SQLiteParameters)

    def __init__(self, key, parameters: ConnectionParameters):
        self.key = key
        self.parameters = parameters
