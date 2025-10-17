#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QMessageBox


class ConfirmPopup(QMessageBox):
    def __init__(self, title, question):
        super().__init__()
        self.setWindowTitle(title)
        self.setText(question)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.setIcon(QMessageBox.Question)

    def user_confirms(self):
        return self.exec() == QMessageBox.StandardButton.Ok
