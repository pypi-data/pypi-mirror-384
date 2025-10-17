#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable

from iocbio.gel.application.image.image import Image
from iocbio.gel.domain.gel_image import GelImage


class ImageRepositoryBackend:
    def get_file(self, gel_image: GelImage, image: Image, callback: Callable) -> Image:
        """
        Supports sync and async operation.

        If image is not available, set its state to ImageState.MISSING and return result.

        If image is available on filesystem, set its file property to the corresponding Path.
        Also set image name property.

        If image has to be fetched, return image with set name property and without its
        file property set. Call later callback with the arguments gel_image_id, file_location when ready. If
        callback is called with empty file_location, it is assumed that the image is missing.
        """
        raise NotImplementedError()
