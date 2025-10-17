#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MeasurementLanes(QWidget):
    """
    Container widget for the measurement lanes table.
    """

    def __init__(self, table):
        super().__init__()

        self.layout = QVBoxLayout()

        title = QLabel("<h2>Measurement Lanes</h2>")
        self.layout.addWidget(title)
        self.layout.addWidget(table)
        self.setLayout(self.layout)
