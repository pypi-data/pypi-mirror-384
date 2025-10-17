#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import shutil
from pathlib import Path

from PySide6.QtWidgets import QFileDialog
from skimage import io

from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.dialogs.select_image import SelectImage
from iocbio.gel.gui.user_resized import UserResized


class SelectImageLocal(QFileDialog, SelectImage, UserResized):
    """
    Local folder image selection dialog.
    """

    def __init__(
        self, gel_image: GelImage, image_source_setup: ImageSourceSetup, settings: SettingsProxy
    ):
        super().__init__()
        UserResized.init(self, settings)

        self.gel_image = gel_image
        self.image_source_setup = image_source_setup
        self.selected_path = None
        self.dir_path = self.image_source_setup.get_local_settings().get("directory")
        if self.dir_path is None:
            raise RuntimeError("Local image provider has missing settings: directory unknown")

        Path(self.dir_path).mkdir(parents=True, exist_ok=True)

        self.setDirectory(self.dir_path)
        if self.gel_image.original_file is not None:
            self.selectFile(str(Path(self.dir_path) / self.gel_image.original_file))

        self.setWindowTitle("Select Image")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setNameFilter("Images (*.tif *.png *.jpg *.jpeg)")
        self.fileSelected.connect(self.on_select)

    def on_select(self, file):
        file = Path(self.move_selected_to_images(file))
        if not file.is_relative_to(self.dir_path):
            self.setResult(0)
            return

        self.selected_path = str(file)
        self.gel_image.clear()
        self.gel_image.original_file = str(file.relative_to(self.dir_path))

    def exec(self):
        result = super(SelectImageLocal, self).exec()
        if result and not self._is_image(self.selected_path):
            self.setResult(0)
        return result

    def move_selected_to_images(self, file) -> Path:
        """
        Relocate files found outside the expected directory since their paths
        are saved relative to that.
        """
        path = Path(file)

        if path.is_relative_to(self.dir_path):
            return path

        new_path = Path(self.dir_path) / path.name
        shutil.copy2(str(path), str(new_path))

        return new_path

    def get_path(self) -> str:
        """
        Set the file on local storage specific gel image parameter.
        """
        return self.selected_path

    def resizeEvent(self, event):
        self.save_geometry()
        super(SelectImageLocal, self).resizeEvent(event)

    @staticmethod
    def _is_image(path):
        try:
            io.imread(path)
            return True
        except (ValueError, SyntaxError, IOError):
            return False
