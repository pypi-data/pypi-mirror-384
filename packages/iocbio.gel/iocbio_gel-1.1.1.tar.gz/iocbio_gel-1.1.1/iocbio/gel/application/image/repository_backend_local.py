#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from pathlib import Path
from typing import Callable

from iocbio.gel.application.image.image import Image
from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.image.image_state import ImageState
from iocbio.gel.application.image.repository_backend import ImageRepositoryBackend
from iocbio.gel.domain.gel_image import GelImage


class ImageRepositoryBackendLocal(ImageRepositoryBackend):
    def __init__(self, image_source_setup: ImageSourceSetup):
        self.image_source_setup = image_source_setup

    def get_file(self, gel_image: GelImage, image: Image, callback: Callable) -> Image:
        images_path = self.image_source_setup.get_local_settings().get("directory")
        if not gel_image.original_file or not images_path:
            image.state = ImageState.MISSING
            return image

        path = Path(images_path, gel_image.original_file)
        image.name = path.name
        image.file = path
        if not path.exists():
            image.state = ImageState.MISSING
        return image
