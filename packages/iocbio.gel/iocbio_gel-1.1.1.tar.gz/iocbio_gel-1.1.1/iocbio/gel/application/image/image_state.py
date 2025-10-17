#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from enum import Enum, auto


class ImageState(Enum):
    LOADING = auto()
    READY = auto()
    MISSING = auto()
