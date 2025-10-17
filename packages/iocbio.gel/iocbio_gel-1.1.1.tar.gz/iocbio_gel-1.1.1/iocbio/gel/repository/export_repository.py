#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import List

from PySide6.QtCore import QObject
from sqlalchemy import select
from sqlalchemy.sql.functions import coalesce

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.domain.gel_image_lane import GelImageLane
from iocbio.gel.domain.measurement import Measurement
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.domain.measurement_lane import (
    MeasurementLane,
    measurement_lane_reference,
    measurement_lane_relative_value,
)
from iocbio.gel.domain.project import path_table, association_table


class ExportRepository(QObject):
    def __init__(self, db: DatabaseClient, application_state: ApplicationState):
        super().__init__()
        self.db = db
        self.application_state = application_state

    def fetch_gels(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id,
                Gel.name,
                Gel.ref_time,
                Gel.comment,
                coalesce(path_table.c.path, "").label("project"),
            )
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
        )

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_measurement_types(self) -> tuple[List[str], List]:
        stmt = select(MeasurementType.id, MeasurementType.name, MeasurementType.comment)

        stmt = stmt.order_by(MeasurementType.name)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_images(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id.label("gel ID"),
                Gel.name.label("gel name"),
                GelImage.id.label("image ID"),
                GelImage.omero_id.label("OMERO ID"),
                coalesce(GelImage.original_file, "").label("File"),
                GelImage.taken,
            )
            .join(GelImage)
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
        )

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id, GelImage.id)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_gel_lanes(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id.label("gel ID"),
                Gel.name.label("gel name"),
                GelLane.lane.label("lane number"),
                GelLane.protein_weight,
                GelLane.comment,
                GelLane.sample_id.label("sample ID"),
                GelLane.is_reference,
            )
            .join(GelLane)
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
        )

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id, GelLane.lane)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_measurements_raw(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id.label("gel ID"),
                Gel.name.label("gel name"),
                GelImage.id.label("image ID"),
                GelImage.omero_id.label("OMERO ID"),
                coalesce(GelImage.original_file, "").label("file"),
                GelLane.lane.label("lane number"),
                GelLane.protein_weight,
                GelLane.sample_id.label("sample ID"),
                GelLane.is_reference,
                MeasurementType.name.label("measurement type"),
                MeasurementLane.value,
                MeasurementLane.is_success,
                MeasurementLane.comment,
            )
            .join(GelLane)
            .join(GelImage)
            .join(GelImageLane)
            .join(MeasurementLane)
            .join(Measurement)
            .join(MeasurementType)
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
        )

        # required to ensure a correct join
        stmt = stmt.where(GelImageLane.gel_lane_id == GelLane.id)

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id, GelImage.id, MeasurementType.name, GelLane.lane)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_measurements_reference(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id.label("gel ID"),
                Gel.name.label("gel name"),
                GelImage.id.label("image ID"),
                GelImage.omero_id.label("OMERO ID"),
                coalesce(GelImage.original_file, "").label("file"),
                MeasurementType.name.label("measurement type"),
                measurement_lane_reference.c.value_per_protein,
                measurement_lane_reference.c.value_per_protein_min,
                measurement_lane_reference.c.value_per_protein_max,
                measurement_lane_reference.c.n,
            )
            .join(GelImage)
            .join_from(
                GelImage,
                measurement_lane_reference,
                measurement_lane_reference.c.image_id == GelImage.id,
            )
            .join_from(
                measurement_lane_reference,
                Measurement,
                measurement_lane_reference.c.measurement_id == Measurement.id,
            )
            .join(MeasurementType)
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
        )

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id, GelImage.id, MeasurementType.name)

        return stmt.columns.keys(), self.db.execute(stmt).all()

    def fetch_measurements_relative(self) -> tuple[List[str], List]:
        stmt = (
            select(
                Gel.id.label("gel ID"),
                Gel.name.label("gel name"),
                GelImage.id.label("image ID"),
                GelImage.omero_id.label("OMERO ID"),
                coalesce(GelImage.original_file, "").label("file"),
                GelLane.lane.label("lane number"),
                GelLane.protein_weight,
                GelLane.sample_id.label("sample ID"),
                GelLane.is_reference,
                MeasurementType.name.label("measurement type"),
                measurement_lane_relative_value.c.relative_value.label("relative value"),
                MeasurementLane.is_success,
                MeasurementLane.comment,
            )
            .join(GelLane)
            .join(GelImage)
            .join(GelImageLane)
            .join(MeasurementLane)
            .join(Measurement)
            .join(MeasurementType)
            .join_from(Gel, association_table, Gel.id == association_table.c.gel_id, isouter=True)
            .join_from(
                association_table,
                path_table,
                association_table.c.project_id == path_table.c.id,
                isouter=True,
            )
            .join_from(
                MeasurementLane,
                measurement_lane_relative_value,
                measurement_lane_relative_value.c.measurement_lane_id == MeasurementLane.id,
            )
        )

        # required to ensure a correct join
        stmt = stmt.where(GelImageLane.gel_lane_id == GelLane.id)

        if self.application_state.project is not None:
            stmt = stmt.where(path_table.c.path.like(f"{self.application_state.project.path}%"))

        stmt = stmt.order_by(Gel.id, GelImage.id, MeasurementType.name, GelLane.lane)

        return stmt.columns.keys(), self.db.execute(stmt).all()
