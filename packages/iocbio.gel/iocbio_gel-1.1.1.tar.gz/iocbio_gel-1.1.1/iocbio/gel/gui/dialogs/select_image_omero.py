#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QStackedWidget,
    QFormLayout,
    QHBoxLayout,
)
from PySide6.QtGui import QIntValidator

from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.dialogs.select_image import SelectImage
from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.application.thread.fetch_image_from_omero import FetchImageFromOmero
from iocbio.gel.application.thread.thread_pool import ThreadPool
from iocbio.gel.application.event_registry import EventRegistry


class SelectImageOmero(QDialog, SelectImage):
    """
    Omero server image selection dialog.
    """

    def __init__(
        self,
        gel_image: GelImage,
        event_registry: EventRegistry,
        omero_client: OmeroClient,
        thread_pool: ThreadPool,
    ):
        super().__init__()

        self.setWindowTitle("Fetch image by Omero ID")

        self.logger = logging.getLogger(__name__)
        self.event_registry = event_registry
        self.gel_image = gel_image
        self.client = omero_client
        self.thread_pool = thread_pool
        self.selected_image = None
        self.selected_id = None

        self.layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.image_id_field = QLineEdit()
        self.image_id_field.setValidator(QIntValidator(bottom=0))
        if self.gel_image.omero_id is not None:
            self.image_id_field.setText(str(self.gel_image.omero_id))
        form_layout.addRow("Omero ID: ", self.image_id_field)
        self.layout.addLayout(form_layout)

        layout_buttons = QHBoxLayout()

        self.ok_button = QDialogButtonBox(QDialogButtonBox.Ok)
        self.ok_button.accepted.connect(self.fetch_image)

        layout_buttons.addWidget(self.ok_button)

        self.cancel_button = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.cancel_button.clicked.connect(self.reject)
        layout_buttons.addWidget(self.cancel_button)

        self.layout.addLayout(layout_buttons)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label_holder = QStackedWidget()
        self.layout.addWidget(self.error_label_holder)
        self.is_error = False

        self.setLayout(self.layout)

        self.event_registry.omero_image_fetched.connect(self.on_fetch_ready)

    def set_error(self, error_msg):
        """
        Display errors to the user.
        """
        self.error_label.setText(error_msg)
        self.error_label_holder.addWidget(self.error_label)
        self.is_error = True
        self.adjustSize()

    def clear_error(self):
        """
        Clear existing errors from view.
        """
        if self.is_error:
            self.error_label_holder.removeWidget(self.error_label)
            self.is_error = False
        self.adjustSize()

    def fetch_image(self):
        """
        Attempt to fetch the image based on user entered image ID.
        """
        self.clear_error()
        if not self.image_id_field.hasAcceptableInput():
            self.set_error("Integer value required")
            return

        try:
            self.selected_id = int(self.image_id_field.text())
        except ValueError:
            self.set_error("Integer value required")
            return

        self.selected_image = self.client.get_image_from_cache(self.selected_id)
        if self.selected_image is not None:
            self.gel_image.clear()
            self.gel_image.omero_id = self.selected_id
            self.accept()
        else:
            job = FetchImageFromOmero(self.selected_id, self.client)
            job.signals.ready.connect(self.event_registry.omero_image_fetched)
            self.ok_button.setEnabled(False)
            self.thread_pool.start(job)

    def get_path(self) -> str:
        return self.selected_image

    def on_fetch_ready(self, image_id, file_location) -> None:
        if self.selected_id is None or self.selected_id != image_id:
            return

        self.ok_button.setEnabled(True)
        if not file_location:
            self.selected_id = None
            self.set_error(
                "Failed to fetch or read image from OMERO. Please try again or check your connection parameters."
            )
            return

        self.selected_image = self.client.get_image_from_cache(self.selected_id)
        if self.selected_image is None:
            self.selected_id = None
            self.set_error("Unexpected error while fetching image")
            return

        self.gel_image.clear()
        self.gel_image.omero_id = self.selected_id
        self.accept()
