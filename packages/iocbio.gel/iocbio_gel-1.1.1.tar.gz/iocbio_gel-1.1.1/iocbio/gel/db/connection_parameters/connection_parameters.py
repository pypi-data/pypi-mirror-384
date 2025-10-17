#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


class ConnectionParameters:
    """
    Interface for database connection parameters.
    """

    @staticmethod
    def to_connection_string(**connection_parameters) -> str:
        raise NotImplementedError

    @staticmethod
    def from_connection_string(connection_string: str) -> dict:
        return {}
