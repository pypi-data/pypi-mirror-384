#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Callable


class Command:
    """
    Interface for a basic command used on history stack.
    """

    def __repr__(self):
        return self.__class__.__name__

    @property
    def should_execute(self) -> bool:
        return True

    def execute(self) -> list[Callable]:
        pass

    def undo(self) -> list[Callable]:
        pass
