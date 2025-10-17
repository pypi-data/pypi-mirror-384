#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import Column, Integer, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor
from iocbio.gel.domain.gel import Gel


class GelLane(Entity, Base):
    """
    Metadata describing the properties of a lane on the physical gel.
    """

    __tablename__ = "gel_lane"

    id = Column(Integer, primary_key=True)
    gel_id = Column(Integer, ForeignKey("gel.id"))
    lane = Column(Integer)
    protein_weight = Column(Float)
    comment = Column(Text)
    sample_id = Column(Text)
    is_reference = Column(Boolean, default=False)

    gel: Gel = relationship("Gel", back_populates="lanes")
    gel_image_lanes = relationship("GelImageLane", back_populates="gel_lane", overlaps="lanes")

    def accept(self, visitor: EntityVisitor):
        for lane in self.gel_image_lanes:
            lane.accept(visitor)
        visitor.visit(self)
