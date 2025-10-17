#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""limit protein to non-negative value

Revision ID: fbf8b6944c61
Revises: nrobvvzilln3
Create Date: 2022-08-16 12:05:26.703251

"""
import os

from alembic import op

from iocbio.gel.db.alembic.execute_sqlfile import execute_sqlfile

# revision identifiers, used by Alembic.
revision = "fbf8b6944c61"
down_revision = "nrobvvzilln3"
branch_labels = None
depends_on = None
basename = os.path.dirname(__file__)


def upgrade():
    is_batch = op.get_context().opts.get("render_as_batch", False)
    if not is_batch:
        op.create_check_constraint("check_protein_is_nonnegative", "gel_lane", "protein_weight>=0")
    else:
        # sqlite is using batch mode and we have to drop and recreate views
        execute_sqlfile(os.path.join(basename, "drop_views_set_1.sql"))

        op.execute("PRAGMA foreign_keys=OFF")
        with op.batch_alter_table("gel_lane") as bop:
            bop.create_check_constraint("check_protein_is_nonnegative", "protein_weight>=0")
        op.execute("PRAGMA foreign_keys=ON")

        execute_sqlfile(os.path.join(basename, "create_views_set_1.sql"))


def downgrade():
    pass
