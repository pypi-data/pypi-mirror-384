#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QWidget

from iocbio.gel.application.settings_proxy import SettingsProxy


class UserResized:
    """
    Decorator for QWidget windows and dialogs
    """

    def init(self, settings: SettingsProxy):
        self.settings = settings
        self.size_key = self.__module__ + "." + self.__class__.__name__

        if not isinstance(self, QWidget):
            raise Exception(self.size_key + " must be an instance of QWidget")

        self.restore_geometry()

    def restore_geometry(self):
        """
        Restore the window size to one previously used by the user.
        """
        geometry = self.settings.get(f"{self.size_key}_geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_geometry(self):
        self.settings.set(f"{self.size_key}_geometry", self.saveGeometry())
