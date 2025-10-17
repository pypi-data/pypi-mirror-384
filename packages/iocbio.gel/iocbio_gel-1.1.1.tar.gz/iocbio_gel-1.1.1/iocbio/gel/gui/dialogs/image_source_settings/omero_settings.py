#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Dict, Union

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget
from PySide6.QtGui import QIntValidator

from iocbio.gel.application.image.image_source_setup import ImageSourceSetup


class OmeroSettings(QWidget):
    """
    Form fields for Omero connection settings.
    """

    def __init__(self, image_source_setup: ImageSourceSetup):
        super().__init__()
        layout = QFormLayout()
        params = image_source_setup.get_omero_settings()

        self.host_edit = QLineEdit()
        self.host_edit.setMaxLength(253)
        self.host_edit.setText(params.get("host"))
        layout.addRow("Host name / address:", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setValidator(QIntValidator(1, 65535, self))
        self.port_edit.setText(str(params.get("port")))
        layout.addRow("Port:", self.port_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setMaxLength(16)
        self.user_edit.setText(str(params.get("username", "")))
        layout.addRow("User:", self.user_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(str(params.get("password", "")))
        layout.addRow("Password:", self.password_edit)

        self.setLayout(layout)

    def get_settings(self) -> Dict[str, Union[str, int]]:
        """
        Get the user-filled field values as a dict.
        """
        host = self.host_edit.text()
        port = int(self.port_edit.text() or ImageSourceSetup.OMERO_DEFAULT_PORT)
        user = self.user_edit.text()
        password = self.password_edit.text()
        return {"host": host, "port": port, "username": user, "password": password}
