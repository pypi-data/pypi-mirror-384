#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import List

from sqlalchemy import Column, Boolean, Integer, Text, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.measurement_lane import MeasurementLane
from iocbio.gel.domain.measurement_type import MeasurementType


class Measurement(Entity, Base):
    """
    Entity grouping a measurement of a specific protein or image attribute.
    """

    __tablename__ = "measurement"
    __table_args__ = (ForeignKeyConstraint(["image_id", "gel_id"], ["image.id", "image.gel_id"]),)

    id = Column(Integer, primary_key=True)
    gel_id = Column(Integer, nullable=False)
    type_id = Column(Integer, ForeignKey("measurement_type.id"))
    image_id = Column(Integer, nullable=False)
    sync_lane_rois = Column(Boolean, default=False)
    comment = Column(Text)

    image: GelImage = relationship("GelImage", back_populates="measurements")
    active_lanes: List[MeasurementLane] = relationship(
        "MeasurementLane", back_populates="measurement", overlaps="image_lane,measurement_lanes"
    )
    measurement_type: MeasurementType = relationship(
        "MeasurementType", back_populates="measurements"
    )

    def accept(self, visitor: EntityVisitor):
        for lane in self.active_lanes:
            lane.accept(visitor)
        visitor.visit(self)
