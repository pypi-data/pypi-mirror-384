#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QPushButton, QFileDialog, QStyle

from iocbio.gel.application.image.image_source_setup import ImageSourceSetup


class LocalSettings(QWidget):
    """
    Settings for local image source
    """

    def __init__(self, image_source_setup: ImageSourceSetup):
        super().__init__()
        layout = QFormLayout()
        params = image_source_setup.get_local_settings()

        self.directory = params["directory"]

        self.label_directory = QLabel(self.directory)
        button = QPushButton(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), "Select directory"
        )
        button.setMaximumWidth(button.sizeHint().width() * 1.25)
        button.clicked.connect(self._on_change)

        layout = QFormLayout()
        layout.addRow("Image directory:", self.label_directory)
        layout.addRow("", button)

        self.setLayout(layout)

    def get_settings(self):
        """
        Get the user-filled field values as a dict.
        """
        return {"directory": self.directory}

    def _on_change(self):
        directory = QFileDialog.getExistingDirectory(
            caption="Select directory with images", dir=self.directory
        )
        if directory:
            self.directory = directory
            self.label_directory.setText(directory)
