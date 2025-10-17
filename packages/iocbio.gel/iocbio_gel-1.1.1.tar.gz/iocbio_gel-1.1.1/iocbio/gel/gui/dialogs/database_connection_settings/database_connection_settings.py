#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QWidget


class DatabaseConnectionSettings(QWidget):
    """
    Interface for implementing database connection settings dialog.
    """

    def __init__(self):
        super().__init__()

    def get_connection_string(self) -> str:
        raise NotImplementedError()
