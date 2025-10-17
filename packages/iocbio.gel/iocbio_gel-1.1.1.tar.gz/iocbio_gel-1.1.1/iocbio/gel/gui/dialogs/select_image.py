#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


class SelectImage:
    """
    Dialog interface for image selection.
    """

    def __init__(self):
        super().__init__()

    def get_path(self) -> str:
        raise NotImplementedError
