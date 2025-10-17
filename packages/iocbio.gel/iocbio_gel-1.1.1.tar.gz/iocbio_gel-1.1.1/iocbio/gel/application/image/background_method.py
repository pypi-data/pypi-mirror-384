#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from enum import Enum


class BackgroundMethod(Enum):
    NONE = "none"
    FLAT = "flat"
    BALL = "ball"
    ELLIPSOID = "ellipsoid"

    @classmethod
    def list(cls):
        return [x.value for x in cls]

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        if other is None and self == BackgroundMethod.NONE:
            return True
        if isinstance(other, str):
            return self.value == other
        return isinstance(other, BackgroundMethod) and self.value == other.value

    def __hash__(self):
        return hash(self.value)
