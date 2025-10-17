#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""projects

Revision ID: fd339f2a6eb4
Revises: fbf8b6944c61
Create Date: 2022-08-09 12:43:41.313239

"""
import os

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
    Computed,
    UniqueConstraint,
    CheckConstraint,
)
from alembic.op import create_table, drop_table, execute

from iocbio.gel.db.alembic.execute_sqlfile import execute_sqlfile


# revision identifiers, used by Alembic.
revision = "fd339f2a6eb4"
down_revision = "fbf8b6944c61"
branch_labels = None
depends_on = None
basename = os.path.dirname(__file__)


def upgrade():
    create_table(
        "project",
        Column("id", Integer(), primary_key=True),
        Column(
            "parent_id",
            Integer(),
            ForeignKey(
                "project.id", name="fk_project_project", ondelete="cascade", onupdate="cascade"
            ),
            nullable=True,
        ),
        Column("name", Text(), nullable=False),
        Column("comment", Text()),
        Column("parent_id_for_constraint", Integer(), Computed("COALESCE(parent_id, -1)")),
        UniqueConstraint("parent_id_for_constraint", "name", name="uc_project_name_per_parent"),
        CheckConstraint("id >= 0", name="check_project_id_is_nonnegative"),
        CheckConstraint("LTRIM(RTRIM(name)) = name", name="check_project_name_is_not_padded"),
    )

    create_table(
        "gel_to_project",
        Column(
            "gel_id",
            Integer(),
            ForeignKey(
                "gel.id", name="fk_gel_to_project_gel", ondelete="cascade", onupdate="cascade"
            ),
            primary_key=True,
        ),
        Column(
            "project_id",
            Integer(),
            ForeignKey(
                "project.id",
                name="fk_gel_to_project_project",
                ondelete="cascade",
                onupdate="cascade",
            ),
            primary_key=True,
        ),
    )
    execute_sqlfile(os.path.join(basename, revision + "_upgrade.sql"))


def downgrade():
    execute("DROP VIEW IF EXISTS project_with_path")
    drop_table("gel_to_project")
    drop_table("project")
