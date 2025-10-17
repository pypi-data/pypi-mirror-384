#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""Create views

Revision ID: nrobvvzilln3
Revises: wrsc7ffn1q95
Create Date: 2022-07-20 16:29:18.118784

"""
import os

from iocbio.gel.db.alembic.execute_sqlfile import execute_sqlfile


# revision identifiers, used by Alembic.
revision = "nrobvvzilln3"
down_revision = "wrsc7ffn1q95"
branch_labels = None
depends_on = None
basename = os.path.dirname(__file__)


def upgrade():
    execute_sqlfile(os.path.join(basename, "create_views_set_1.sql"))


def downgrade():
    execute_sqlfile(os.path.join(basename, "drop_views_set_1.sql"))
