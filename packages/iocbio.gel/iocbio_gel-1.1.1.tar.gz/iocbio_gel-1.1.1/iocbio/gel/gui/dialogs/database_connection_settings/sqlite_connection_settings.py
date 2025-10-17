#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from pathlib import PurePath
from PySide6.QtWidgets import QLabel, QFormLayout, QPushButton, QFileDialog, QStyle
from PySide6.QtCore import QStandardPaths

from iocbio.gel.gui.dialogs.database_connection_settings.database_connection_settings import (
    DatabaseConnectionSettings,
)
from iocbio.gel.db.database_setup import DatabaseSetup
from iocbio.gel.db.connection_parameters.sqlite_parameters import SQLiteParameters as Parameters


class SQLiteConnectionSettings(DatabaseConnectionSettings):
    def __init__(self, db_setup: DatabaseSetup, data_directory: str):
        super().__init__()
        params = Parameters.from_connection_string(db_setup.get_connection_string())
        directory = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        self.path = params.get("path", str(PurePath(directory) / "iocbio_gel.db"))

        self.label_path = QLabel(str(self.path))
        button = QPushButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), "Select file"
        )
        button.setMaximumWidth(button.sizeHint().width() * 1.25)
        button.clicked.connect(self._on_change)

        layout = QFormLayout()
        layout.addRow("Path:", self.label_path)
        layout.addRow("", button)

        self.setLayout(layout)

    def get_connection_string(self) -> str:
        return Parameters().to_connection_string(path=self.path)

    def _on_change(self):
        dialog = QFileDialog(caption="Select SQLite database file", filter="SQLite (*.db)")
        dialog.selectFile(str(self.path))
        dialog.setDirectory(str(PurePath(self.path).parent))
        dialog.setDefaultSuffix("db")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setOption(QFileDialog.DontConfirmOverwrite)
        if dialog.exec():
            self.path = dialog.selectedFiles()[0]
            self.label_path.setText(self.path)
