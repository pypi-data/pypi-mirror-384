#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Dict, Union, Optional

from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.application.image.image_source import ImageSource


class ImageSourceSetup:
    """
    Currently implements only Omero image source settings.
    """

    LOCAL_PREFIX = "image_source/local"
    OMERO_DEFAULT_PORT = 4064
    OMERO_PREFIX = "image_source/omero"
    SOURCE_TYPE = "image_source/type"

    def __init__(self, default_local_directory: str, settings: SettingsProxy) -> None:
        self.settings = settings
        self.default_local_directory = default_local_directory

    def get_local_settings(self) -> Dict[str, str]:
        prefix = self.LOCAL_PREFIX
        return {"directory": self.settings.get(f"{prefix}/directory", self.default_local_directory)}

    def set_local_settings(self, directory) -> None:
        prefix = self.LOCAL_PREFIX
        self.settings.set(f"{prefix}/directory", directory)

    def get_omero_settings(self) -> Dict[str, Union[int, str]]:
        settings = self.settings
        prefix = self.OMERO_PREFIX

        return {
            "username": settings.get(f"{prefix}/username", secure=True),
            "password": settings.get(f"{prefix}/password", secure=True),
            "host": settings.get(f"{prefix}/host"),
            "port": settings.get(f"{prefix}/port", self.OMERO_DEFAULT_PORT),
        }

    def set_omero_settings(self, username, password, host, port) -> None:
        settings = self.settings
        prefix = self.OMERO_PREFIX

        settings.set(f"{prefix}/username", username, secure=True)
        settings.set(f"{prefix}/password", password, secure=True)
        settings.set(f"{prefix}/host", host)
        settings.set(f"{prefix}/port", port)

    def clear_omero_login(self):
        settings = self.settings
        prefix = self.OMERO_PREFIX

        settings.remove(f"{prefix}/username", secure=True)
        settings.remove(f"{prefix}/password", secure=True)

    def get_type(self) -> Optional[ImageSource]:
        if not self.settings.contains(self.SOURCE_TYPE):
            return None
        if self.settings.get(self.SOURCE_TYPE) in ImageSource.__members__:
            return ImageSource[self.settings.get(self.SOURCE_TYPE)]
        return None

    def set_type(self, source_type: ImageSource) -> None:
        self.settings.set(self.SOURCE_TYPE, source_type.name)
