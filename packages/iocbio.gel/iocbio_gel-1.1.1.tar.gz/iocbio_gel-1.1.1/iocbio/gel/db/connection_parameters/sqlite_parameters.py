#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from iocbio.gel.db.connection_parameters.connection_parameters import ConnectionParameters


class SQLiteParameters(ConnectionParameters):
    @staticmethod
    def to_connection_string(path) -> str:
        return "sqlite:///" + path

    @staticmethod
    def from_connection_string(connection_string: str) -> dict:
        if not connection_string or not connection_string.startswith("sqlite"):
            return {}
        return dict(path=connection_string[10:])
