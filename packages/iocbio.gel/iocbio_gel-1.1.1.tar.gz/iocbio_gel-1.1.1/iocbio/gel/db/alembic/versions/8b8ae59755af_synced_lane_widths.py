#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""synced_lane_widths

Revision ID: 8b8ae59755af
Revises: fd339f2a6eb4
Create Date: 2022-09-02 09:07:46.362538

"""
from sqlalchemy import Column, Boolean

from alembic.op import add_column, drop_column

# revision identifiers, used by Alembic.
revision = "8b8ae59755af"
down_revision = "fd339f2a6eb4"
branch_labels = None
depends_on = None


def upgrade():
    add_column(
        "image",
        Column("sync_lane_widths", Boolean(), nullable=False, default=False, server_default="0"),
    )


def downgrade():
    drop_column("image", "sync_lane_widths")
