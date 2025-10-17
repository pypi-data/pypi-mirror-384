#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import logging
import traceback

from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QLabel, QStackedWidget, QVBoxLayout

from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.application.image.image_source import ImageSource
from iocbio.gel.gui.dialogs.image_source_settings.local_settings import LocalSettings
from iocbio.gel.gui.dialogs.image_source_settings.omero_settings import OmeroSettings


class ImageSourceForm(QVBoxLayout):
    """
    Form for selecting the image source option and filling in connection parameters.
    """

    def __init__(
        self,
        image_source_setup: ImageSourceSetup,
        omero_client: OmeroClient,
        accept_callback,
        change_callback,
    ):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.image_source_setup = image_source_setup
        self.omero_client = omero_client
        self.accept_callback = accept_callback
        self.change_callback = change_callback

        help_txt = (
            "IOCBIO Gel analyzes images that can be either accessed as files in PC or "
            + "through OMERO server. \n\n"
            + "When images are available as files on PC, choose 'Local files' below. "
            + "This includes files stored locally on your PC, "
            + "as well as files available through centralized network storage and mounted on your PC. "
            + "If you want to access images as 'Local files' then select the directory where the images "
            + "or directory hierarchy with the images are."
            + " For example, if you have a directory 'Gel images' "
            + "which has subdirectories organized by date and images under it (as in 22.11.30/gel1.tif) then "
            + "you can select 'Gel images' as a directory. IOCBIO Gel will then store only relative "
            + "path of the image in its database.\n\n"
            + "As an alternative to storing images in folders, you can also use OMERO (specialized image server) "
            + " to keep the images. While "
            + "OMERO is developed to keep microscopy images, it can store images obtained for other applications "
            + "as well."
            + "\n"
        )
        help = QLabel(help_txt)
        help.setWordWrap(True)
        self.addWidget(help)

        self.settings_widgets = {
            ImageSource.LOCAL.value: LocalSettings(image_source_setup),
            ImageSource.OMERO.value: OmeroSettings(image_source_setup),
        }
        self.current_settings_widget = None

        self.selection_box = QComboBox()
        self.addWidget(self.selection_box)

        self.selection_widget = QStackedWidget()
        self.addWidget(self.selection_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.on_accept)
        self.addWidget(self.button_box)

        self.error_label = QLabel()
        self.error_label_holder = QStackedWidget()
        self.addWidget(self.error_label_holder)
        self.is_error = False

        self.selection_box.currentTextChanged.connect(self.on_selection_changed)
        self.selection_box.addItems([img_src.value for img_src in ImageSource])

        current_type = self.image_source_setup.get_type()
        if current_type is not None:
            self.selection_box.setCurrentText(current_type.value)

    def clear_error(self):
        """
        Clear previous error message.
        """
        if self.is_error:
            self.error_label_holder.removeWidget(self.error_label)
            self.is_error = False

    def set_error(self, message):
        """
        Display error message to the user.
        """
        self.error_label.setText(message)
        self.error_label_holder.addWidget(self.error_label)
        self.is_error = True

    def on_selection_changed(self, selection):
        """
        Change the fields visible based on the selected image source.
        """
        self.clear_error()
        if self.current_settings_widget:
            self.selection_widget.removeWidget(self.current_settings_widget)
        self.current_settings_widget = self.settings_widgets[selection]
        self.selection_widget.addWidget(self.current_settings_widget)

        self.change_callback()

    def on_accept(self):
        """
        Check external image source connection before allowing the user to proceed.
        """
        self.clear_error()

        source_type = ImageSource(value=self.selection_box.currentText())
        self.image_source_setup.set_type(source_type)

        if source_type == ImageSource.LOCAL:
            self.image_source_setup.set_local_settings(
                **self.settings_widgets[source_type.value].get_settings()
            )
            self.accept_callback()
            return

        if source_type == ImageSource.OMERO:
            self.image_source_setup.set_omero_settings(
                **self.settings_widgets[source_type.value].get_settings()
            )

            try:
                self.omero_client.start_session()
                self.accept_callback()
            except ConnectionError as e:
                self.set_error(str(e))
                self.logger.debug(traceback.format_exc())
