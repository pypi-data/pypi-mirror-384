#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import Column, Integer, Text, Boolean, Float, ForeignKeyConstraint, MetaData, Table
from sqlalchemy.orm import relationship, validates

from iocbio.gel.db.base import Base, Entity

metadata_obj = MetaData()

measurement_lane_reference = Table(
    "measurement_reference_value",
    metadata_obj,
    Column("measurement_id", Integer),
    Column("image_id", Integer),
    Column("value_per_protein", Float),
    Column("value_per_protein_min", Float),
    Column("value_per_protein_max", Float),
    Column("n", Integer),
)

measurement_lane_relative_value = Table(
    "measurement_relative_value",
    metadata_obj,
    Column("gel_lane_id", Integer),
    Column("measurement_lane_id", Integer),
    Column("relative_value", Float),
)


class MeasurementLane(Entity, Base):
    """
    Measured intensity value for a user-selected lane.
    """

    __tablename__ = "measurement_lane"
    __table_args__ = (
        ForeignKeyConstraint(
            ["image_lane_id", "gel_id", "image_id"],
            ["image_lane.id", "image_lane.gel_id", "image_lane.image_id"],
        ),
        ForeignKeyConstraint(
            ["measurement_id", "gel_id", "image_id"],
            ["measurement.id", "measurement.gel_id", "measurement.image_id"],
        ),
    )

    id = Column(Integer, primary_key=True)
    gel_id = Column(Integer, nullable=False)
    image_id = Column(Integer, nullable=False)
    image_lane_id = Column(Integer, nullable=False)
    measurement_id = Column(Integer, nullable=False)
    value = Column(Float)
    min = Column(Integer)
    max = Column(Integer)
    comment = Column(Text)
    is_success = Column(Boolean, nullable=False, default=True)

    measurement = relationship(
        "Measurement", back_populates="active_lanes", overlaps="measurement_lanes"
    )
    image_lane = relationship(
        "GelImageLane", back_populates="measurement_lanes", overlaps="measurement"
    )

    @property
    def lane(self):
        return self.image_lane.gel_lane.lane

    @validates("value")
    def validate_value(self, key, value):
        return float(value)
