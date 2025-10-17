#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QComboBox, QFormLayout, QLineEdit
from PySide6.QtGui import QIntValidator

from iocbio.gel.db.database_setup import DatabaseSetup
from iocbio.gel.gui.dialogs.database_connection_settings.database_connection_settings import (
    DatabaseConnectionSettings,
)
from iocbio.gel.db.connection_parameters.postgresql_parameters import (
    PostgreSQLParameters as Parameters,
)


class PostgreSQLConnectionSettings(DatabaseConnectionSettings):
    """
    Form fields for PostgreSQL connection parameters.
    """

    PORT_DEFAULT = "5432"
    SSL_OPTIONS = ["prefer", "disable", "allow", "require", "verify-ca", "verify-full"]
    SCHEMA_DEFAULT = "gel"

    def __init__(self, db_setup: DatabaseSetup):
        super().__init__()
        layout = QFormLayout()

        params = Parameters.from_connection_string(db_setup.get_connection_string())

        self.host_edit = QLineEdit()
        self.host_edit.setMaxLength(253)
        self.host_edit.setText(params.get("host", "localhost"))
        layout.addRow("Host name / address:", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setValidator(QIntValidator(1, 65535, self))
        self.port_edit.setText(params.get("port", self.PORT_DEFAULT))
        layout.addRow("Port:", self.port_edit)

        self.ssl_mode_selection = QComboBox()
        self.ssl_mode_selection.addItems(self.SSL_OPTIONS)
        self.ssl_mode_selection.setCurrentText(params.get("ssl", self.SSL_OPTIONS[0]))
        layout.addRow("SSL mode:", self.ssl_mode_selection)

        self.database_edit = QLineEdit()
        self.database_edit.setMaxLength(63)
        self.database_edit.setText(params.get("db", ""))
        layout.addRow("Database:", self.database_edit)

        self.schema_edit = QLineEdit()
        self.schema_edit.setMaxLength(63)
        self.schema_edit.setText(params.get("schema", self.SCHEMA_DEFAULT))
        layout.addRow("Schema:", self.schema_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setMaxLength(16)
        self.user_edit.setText(params.get("user", ""))
        layout.addRow("User:", self.user_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(params.get("password", ""))
        layout.addRow("Password:", self.password_edit)

        self.setLayout(layout)

    def get_connection_string(self) -> str:
        """
        Get the connection string from user-filled fields.
        """
        host = self.host_edit.text()
        port = self.port_edit.text()
        user = self.user_edit.text()
        password = self.password_edit.text()
        db_name = self.database_edit.text()
        schema = self.schema_edit.text()
        ssl_mode = self.ssl_mode_selection.currentText()

        return Parameters.to_connection_string(
            host=host,
            port=port,
            user=user,
            password=password,
            db_name=db_name,
            schema=schema,
            ssl_mode=ssl_mode,
        )
