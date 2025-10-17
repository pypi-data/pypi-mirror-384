#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QLabel, QStackedWidget, QVBoxLayout

from iocbio.gel.db.database_setup import DatabaseSetup
from iocbio.gel.db.database_type import DatabaseType
from iocbio.gel.gui.dialogs.database_connection_settings.postgresql_connection_settings import (
    PostgreSQLConnectionSettings,
)
from iocbio.gel.gui.dialogs.database_connection_settings.sqlite_connection_settings import (
    SQLiteConnectionSettings,
)


class DbSelectionForm(QVBoxLayout):
    """
    Form for selecting the database option and filling in connection parameters.
    """

    def __init__(
        self,
        db_setup: DatabaseSetup,
        sql_lite_settings: SQLiteConnectionSettings,
        accept_callback,
        change_callback,
    ):
        super().__init__()
        self.db_setup = db_setup
        self.accept_callback = accept_callback
        self.change_callback = change_callback

        self.settings_widgets = {
            DatabaseType.POSTGRESQL.key: PostgreSQLConnectionSettings(self.db_setup),
            DatabaseType.SQLITE.key: sql_lite_settings,
        }
        self.current_settings_widget = None
        self.current_key = None

        help_txt = (
            "IOCBIO Gel stores information regarding gels, lanes, and measurement results in the database. "
            + "Two database types are supported: SQLite and PostgreSQL. "
            + "Regardless of the database type, you can always export data into the spreadsheet.\n\n"
            + "Out of these database types, SQLite is a local database contained in a single file. "
            + "SQLite is suitable if you wish to work on your gels in a single PC or manually move files "
            + "between PCs.\n\n"
            + "PostgreSQL is usually preferred if you want to keep your data centrally. "
            + "By keeping data centrally in PostgreSQL, it is easier to collaborate within "
            + "the research team by sharing the original data and it's analysis. "
            + "However, PostgreSQL would require a setup of a central server and, to access it from outside of campus, "
            + "probably a VPN service.\n"
        )
        help = QLabel(help_txt)
        help.setWordWrap(True)
        self.addWidget(help)

        self.db_selection = QComboBox()
        self.addWidget(self.db_selection)

        self.db_selection_holder = QStackedWidget()
        self.addWidget(self.db_selection_holder)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.on_accept)
        self.addWidget(self.button_box)

        self.error_label = QLabel()
        self.error_label_holder = QStackedWidget()
        self.addWidget(self.error_label_holder)
        self.is_error = False

        self.db_selection.currentTextChanged.connect(self.on_db_selection_changed)
        self.db_selection.addItems([db.key for db in DatabaseType])
        self.select_type_from_settings()

    def select_type_from_settings(self):
        current_type = self.db_setup.get_connection_type()
        if current_type is None:
            current_type = DatabaseType.SQLITE.key
        self.db_selection.setCurrentText(current_type)

    def clear_error(self):
        """
        Clear previous error message.
        """
        if self.is_error:
            self.error_label_holder.removeWidget(self.error_label)
            self.is_error = False

    def set_error(self, message):
        """
        Display error message to the user.
        """
        self.error_label.setText(message)
        self.error_label_holder.addWidget(self.error_label)
        self.is_error = True

    def on_db_selection_changed(self, db):
        """
        Change the fields visible based on the selected database.
        """
        self.clear_error()
        if self.current_settings_widget:
            self.db_selection_holder.removeWidget(self.current_settings_widget)
        self.current_settings_widget = self.settings_widgets[db]
        self.db_selection_holder.addWidget(self.current_settings_widget)
        self.current_key = db

        self.change_callback()

    def on_accept(self):
        """
        Check the connection before allowing the user to proceed.
        """
        self.clear_error()
        try:
            connection_string = self.current_settings_widget.get_connection_string()
            self.db_setup.set_connection_type(self.current_key)
            self.db_setup.migrate_database(connection_string)
            self.accept_callback()
        except Exception as e:
            self.set_error(str(e))
