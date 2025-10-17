#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import os

from alembic import command
from alembic.config import Config

from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.db.database_type import DatabaseType


class DatabaseSetup:
    """
    Mediates database connection settings and migrations.
    """

    CONNECTION_STRING_KEY = "database_connection_string"
    CONNECTION_TYPE_KEY = "database_connection_type"

    def __init__(self, settings: SettingsProxy) -> None:
        self.settings = settings

    def migrate_database(self, connection_string=None):
        """
        Applies database migrations if the version_number in the alembic_version table differs from the latest
        migration file.
        """
        connection_string = connection_string or self.get_connection_string()
        schema = self.get_schema(connection_string)
        root_directory = os.path.dirname(os.path.abspath(__file__))
        alembic_directory = os.path.join(root_directory, "alembic")
        ini_path = os.path.join(root_directory, "alembic", "alembic.ini")
        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("script_location", alembic_directory)
        alembic_cfg.set_main_option("sqlalchemy.url", connection_string)
        alembic_cfg.set_main_option("gel.database.schema", schema)
        command.upgrade(alembic_cfg, "head")
        self.settings.set(self.CONNECTION_STRING_KEY, connection_string, secure=True)

    def get_connection_string(self):
        return self.settings.get(self.CONNECTION_STRING_KEY, None, secure=True)

    def has_connection_string(self):
        return self.settings.contains(self.CONNECTION_STRING_KEY, secure=True)

    def clear_connection_string(self):
        self.settings.remove(self.CONNECTION_STRING_KEY, secure=True)

    def set_connection_type(self, connection_type):
        self.settings.set(self.CONNECTION_TYPE_KEY, connection_type)

    def get_connection_type(self):
        return self.settings.get(self.CONNECTION_TYPE_KEY, None)

    def get_schema(self, connection_string):
        connection_type = self.get_connection_type()
        if not connection_type:
            return ""

        return (
            DatabaseType[connection_type.upper()]
            .parameters.from_connection_string(connection_string)
            .get("schema", "")
        )
