#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from iocbio.gel.db.base import Entity


class EntityVisitor:
    def visit(self, entity: Entity):
        raise NotImplementedError
