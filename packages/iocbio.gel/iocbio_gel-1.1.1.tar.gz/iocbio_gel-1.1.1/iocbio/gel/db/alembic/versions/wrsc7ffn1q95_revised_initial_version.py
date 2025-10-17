#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""Revised initial version

Revision ID: wrsc7ffn1q95
Revises:
Create Date: 2022-07-27 08:14:20.153993

"""
import sqlalchemy as sa

from alembic import op
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = "wrsc7ffn1q95"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gel",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("transfer", sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column("comment", sa.Text()),
    )

    op.create_table(
        "gel_lane",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "gel_id",
            sa.Integer(),
            sa.ForeignKey("gel.id", name="fk_gel_lane_gel", ondelete="cascade", onupdate="cascade"),
            nullable=False,
        ),
        sa.Column("lane", sa.Integer(), nullable=False),
        sa.Column("protein_weight", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("sample_id", sa.Text()),
        sa.Column("is_reference", sa.Boolean(), default=False),
        UniqueConstraint("id", "gel_id", name="uc_gel_lane_composed_key"),
        UniqueConstraint("lane", "gel_id", name="uc_gel_lane_unique"),
        CheckConstraint("lane > 0", name="check_lane_is_positive"),
    )

    op.create_table(
        "image",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "gel_id",
            sa.Integer(),
            sa.ForeignKey("gel.id", name="fk_image_gel", ondelete="cascade", onupdate="cascade"),
            nullable=False,
        ),
        sa.Column("original_file", sa.Text(), nullable=True),
        sa.Column("omero_id", sa.Integer(), nullable=True),
        sa.Column("hash", sa.Text(), nullable=False),
        sa.Column("taken", sa.DateTime(), server_default=func.now()),
        sa.Column("region", sa.Text()),
        sa.Column("rotation", sa.Float()),
        sa.Column("background_subtraction", sa.Text()),
        sa.Column("background_is_dark", sa.Boolean(), default=False),
        sa.Column("colormap_min", sa.Float(), nullable=True),
        sa.Column("colormap_max", sa.Float(), nullable=True),
        UniqueConstraint("id", "gel_id", name="uc_image_composed_key"),
        CheckConstraint("colormap_min < colormap_max", name="check_colormap_min_less_than_max"),
        CheckConstraint("original_file IS NULL OR omero_id IS NULL", name="check_one_image"),
    )

    op.create_table(
        "image_lane",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gel_id", sa.Integer(), nullable=False),
        sa.Column("image_id", sa.Integer(), nullable=False),
        sa.Column("gel_lane_id", sa.Integer(), nullable=False),
        sa.Column("region", sa.Text()),
        sa.Column("zero_line_points", sa.Text(), nullable=True),
        UniqueConstraint("id", "gel_id", "image_id", name="uc_image_lane_composed_key"),
        UniqueConstraint("gel_id", "gel_lane_id", "image_id", name="uc_image_lane_unique"),
        sa.ForeignKeyConstraint(
            ["image_id", "gel_id"],
            ["image.id", "image.gel_id"],
            name="fk_image_lane_image",
            ondelete="cascade",
            onupdate="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["gel_lane_id", "gel_id"],
            ["gel_lane.id", "gel_lane.gel_id"],
            name="fk_image_lane_gel_lane",
            ondelete="cascade",
            onupdate="cascade",
        ),
    )

    op.create_table(
        "measurement_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text()),
        UniqueConstraint("name", name="uc_measurement_type_name_unique"),
    )

    op.create_table(
        "measurement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gel_id", sa.Integer(), nullable=False),
        sa.Column(
            "type_id",
            sa.Integer(),
            sa.ForeignKey("measurement_type.id", name="fk_measurement_measurement_type"),
            nullable=False,
        ),
        sa.Column("image_id", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        UniqueConstraint("id", "gel_id", "image_id", name="uc_measurement_composed_key"),
        UniqueConstraint("type_id", "image_id", name="uc_measurement_unique_for_image"),
        sa.ForeignKeyConstraint(
            ["image_id", "gel_id"],
            ["image.id", "image.gel_id"],
            name="fk_measurement_image",
            ondelete="cascade",
            onupdate="cascade",
        ),
    )

    op.create_table(
        "measurement_lane",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gel_id", sa.Integer(), nullable=False),
        sa.Column("image_id", sa.Integer(), nullable=False),
        sa.Column("image_lane_id", sa.Integer(), nullable=False),
        sa.Column("measurement_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("min", sa.Integer(), default=0),
        sa.Column("max", sa.Integer()),
        sa.Column("comment", sa.Text()),
        sa.Column("is_success", sa.Boolean(), default=True, nullable=False),
        UniqueConstraint(
            "gel_id", "image_lane_id", "measurement_id", name="uc_measurement_lane_unique"
        ),
        sa.ForeignKeyConstraint(
            ["image_lane_id", "gel_id", "image_id"],
            ["image_lane.id", "image_lane.gel_id", "image_lane.image_id"],
            name="fk_measurement_lane_image_lane",
            ondelete="cascade",
            onupdate="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["measurement_id", "gel_id", "image_id"],
            ["measurement.id", "measurement.gel_id", "measurement.image_id"],
            name="fk_measurement_lane_measurement",
            ondelete="cascade",
            onupdate="cascade",
        ),
    )


def downgrade():
    op.drop_table("measurement_lane_plot")
    op.drop_table("measurement_lane")
    op.drop_table("measurement")
    op.drop_table("measurement_type")
    op.drop_table("gel_image_lane")
    op.drop_table("gel_image")
    op.drop_table("gel_lane")
    op.drop_table("gel")
