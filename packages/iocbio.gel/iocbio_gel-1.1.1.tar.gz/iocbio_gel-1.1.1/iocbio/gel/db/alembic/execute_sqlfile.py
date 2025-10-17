#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import sqlparse

from alembic import op


def execute_sqlfile(filename: str) -> None:
    for s in sqlparse.parsestream(open(filename, "r")):
        statement = str(s).strip()
        op.execute(statement)
