#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import hashlib


class FileDigest:
    BUFFER_SIZE = 65536

    @staticmethod
    def get_hex(file_path) -> str:
        """
        Create a SHA256 hex digest from a file.
        :ref:`Example from https://stackoverflow.com/questions/22058048/hashing-a-file-in-python@answer-22058673`
        """
        module = hashlib.sha256()

        with open(file_path, "rb") as f:
            while True:
                data = f.read(FileDigest.BUFFER_SIZE)
                if not data:
                    break
                module.update(data)

        return module.hexdigest()
