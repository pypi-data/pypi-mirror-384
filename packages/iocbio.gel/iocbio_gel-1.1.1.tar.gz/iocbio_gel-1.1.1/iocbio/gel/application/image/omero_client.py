#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import imageio as iio
import logging
import os
import shutil

import Ice
import omero
from omero.gateway import BlitzGateway

from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.application.image.image_source import ImageSource


class OmeroClient:
    """
    Wrapper around Omero library for fetching images.
    """

    OMERO_PATH = "omero"
    SETTINGS_PREFIX = "image_source/omero"
    FAILED_TO_CONNECT_ERROR = (
        "Unable to connect to Omero at {}. Please check your connection parameters."
    )

    def __init__(
        self, image_source_setup: ImageSourceSetup, db_client: DatabaseClient, cache_path: str
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.setup = image_source_setup
        self.db_client = db_client
        self.cache_path = cache_path
        self.image_cache_path = os.path.join(cache_path, self.OMERO_PATH)
        self.session = None

    def start_session(self) -> None:
        """
        Verifies the connection parameters and refreshes image cache files.
        """
        self.close_session()

        settings = self.setup.get_omero_settings()

        try:
            session = BlitzGateway(
                settings["username"],
                settings["password"],
                host=settings["host"],
                port=settings["port"],
            )

            success = session.connect()
        except (
            Ice.ConnectionRefusedException,
            Ice.ConnectionLostException,
            Ice.EndpointParseException,
            omero.ClientError,
        ) as e:
            self.logger.warning("Error from BlitzGateway: " + str(e))
            raise ConnectionError(self.FAILED_TO_CONNECT_ERROR.format(settings["host"]))

        if not success:
            raise ConnectionError(self.FAILED_TO_CONNECT_ERROR.format(settings["host"]))

        session.c.enableKeepAlive(60)
        self.session = session
        self.image_cache_path = self._host_cache_path(settings["host"])

    def is_active(self) -> bool:
        return self.setup.get_type() == ImageSource.OMERO

    def has_session(self) -> bool:
        return self.session is not None

    def close_session(self):
        if self.session is not None:
            self.session.close()

    def get_image_from_cache(self, image_id: int) -> str:
        """
        Fetch image from local cache by OMERO image ID.
        """
        path = self._cache_file_path(image_id)
        if os.path.exists(path):
            return path
        return None

    def get_image(self, image_id: int, use_cache=True) -> str:
        """
        Fetch image from local cache or OMERO server by OMERO image ID.
        Images from Omero are always expected to be in tiff format.
        """
        if not os.path.exists(self.image_cache_path):
            os.makedirs(self.image_cache_path)

        image_location = self._cache_file_path(image_id)
        if use_cache and os.path.exists(image_location):
            return image_location

        image = self.session.getObject("Image", image_id)
        if image is None:
            raise ValueError("Unable to find image with ID {}".format(image_id))

        # code is based on omero.plugins.download
        fileset = image.getFileset()
        image_location_tmp = image_location + "-tmp"
        for orig_file in fileset.listFiles():
            self.session.c.download(orig_file._obj, image_location_tmp)
            iio.imread(image_location_tmp)
            shutil.move(image_location_tmp, image_location)

        return image_location

    def _cache_file_path(self, image_id: int) -> str:
        return os.path.join(self.image_cache_path, f"{image_id}")

    def _host_cache_path(self, host):
        """
        Cache is Omero host specific.
        """
        return os.path.join(
            self.cache_path, self.OMERO_PATH, "".join(x for x in host if x.isalnum())
        )
