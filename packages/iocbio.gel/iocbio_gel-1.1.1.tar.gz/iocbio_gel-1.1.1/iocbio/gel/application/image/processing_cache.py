#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import hashlib
from pathlib import Path
from typing import Optional

import numpy as np

from iocbio.gel.domain.gel_image import GelImage


class ProcessingCache:
    """
    Cache processed image matrices to speed up UX.
    """

    PROCESSING_PATH = "processing"

    @staticmethod
    def background_key(gel_image: GelImage) -> Optional[str]:
        return "{}/{}/{}/{}/{}".format(
            gel_image.hash,
            gel_image.region,
            gel_image.rotation,
            gel_image.background_subtraction,
            gel_image.background_is_dark,
        )

    @staticmethod
    def region_key(gel_image: GelImage) -> Optional[str]:
        return "{}/{}/{}".format(gel_image.hash, gel_image.region, gel_image.rotation)

    def __init__(self, cache_path: str):
        self.cache_path = Path(cache_path) / self.PROCESSING_PATH
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str):
        """
        Loads step numpy matrix from a cache file.
        """
        if key is None:
            return None

        filepath = self._get_file_path(key)
        if not filepath.exists():
            return None

        with open(filepath, "rb") as f:
            return np.load(f, allow_pickle=True)

    def set(self, key: str, data):
        """
        Saves step numpy matrix to a cache file.
        """
        if key is None:
            return

        filepath = self._get_file_path(key)
        if filepath.exists():
            filepath.unlink()

        with open(filepath, "wb") as f:
            np.save(f, data)

    def get_cache_size(self) -> int:
        """
        Returns the total size of cache files in bytes.
        """
        total_size = 0
        if self.cache_path.exists():
            for filepath in self.cache_path.iterdir():
                if filepath.is_file():
                    total_size += filepath.stat().st_size
        return total_size

    def clear_cache(self):
        """
        Removes all cache files.
        """
        if self.cache_path.exists():
            for filepath in self.cache_path.iterdir():
                if filepath.is_file():
                    filepath.unlink()

    def _get_file_path(self, param: str) -> Path:
        file_name = hashlib.sha256(param.encode("utf-8")).hexdigest()
        return self.cache_path / (file_name + ".npy")
