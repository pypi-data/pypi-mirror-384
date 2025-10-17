#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QGroupBox, QRadioButton, QVBoxLayout


class BgColorBox(QGroupBox):
    """
    Widget for selecting between light and dark image background.
    """

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.is_dark_button = QRadioButton("is dark")
        self.is_light_button = QRadioButton("is light")
        self.is_light_button.setChecked(True)

        layout = QVBoxLayout()
        layout.addWidget(self.is_dark_button)
        layout.addWidget(self.is_light_button)
        self.setLayout(layout)

    def set_dark(self, is_dark):
        self.is_dark_button.setChecked(is_dark)

    def is_dark(self):
        return self.is_dark_button.isChecked()
