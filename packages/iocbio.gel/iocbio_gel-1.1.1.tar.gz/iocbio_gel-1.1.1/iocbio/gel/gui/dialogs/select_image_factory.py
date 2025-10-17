#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from iocbio.gel.application.image.image_source import ImageSource
from iocbio.gel.gui.dialogs.select_image import SelectImage
from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.domain.gel_image import GelImage


class SelectImageFactory:
    """
    Factory for providing image selection dialogs based on settings.
    """

    def __init__(self, local, omero, image_source_setup: ImageSourceSetup):
        super().__init__()

        self.providers = {ImageSource.LOCAL: local, ImageSource.OMERO: omero}

        self.setup = image_source_setup

    def create(self, gel_image: GelImage) -> SelectImage:
        return self.providers[self.setup.get_type()](gel_image=gel_image)
