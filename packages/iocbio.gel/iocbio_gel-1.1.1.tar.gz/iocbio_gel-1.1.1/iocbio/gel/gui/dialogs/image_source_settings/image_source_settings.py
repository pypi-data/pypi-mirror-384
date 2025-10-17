#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QDialog, QLayout


class ImageSourceSelectionDialog(QDialog):
    """
    Dialog popup for configuring the image source parameters during the application startup.
    """

    def __init__(self, form_provider):
        super().__init__()
        self.setWindowTitle("Application image source configuration")
        self.layout = form_provider(accept_callback=self.accept, change_callback=self.adjustSize)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.layout)

    def set_error(self, message):
        self.layout.set_error(message)
