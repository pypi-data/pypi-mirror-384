#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import Column, Integer, DateTime, Text, func
from sqlalchemy.orm import relationship

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor


class Gel(Entity, Base):
    """
    Metadata describing the physical gel.
    Ref_time specifies the datetime which is used as a reference. For example,
    when the samples were transferred on the gel.
    """

    __tablename__ = "gel"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    ref_time = Column(DateTime, default=func.now())
    comment = Column(Text)

    lanes = relationship("GelLane", back_populates="gel")
    gel_images = relationship("GelImage", back_populates="gel")
    projects = relationship(
        "iocbio.gel.domain.project.Project",
        secondary="gel_to_project",
        back_populates="gels",
        order_by="asc(iocbio.gel.domain.project.Project.path)",
    )

    @property
    def lanes_count(self):
        return len(self.lanes)

    def get_next_lane(self) -> int:
        """
        Returns the next free lanes index
        """
        return 1 + max([lane.lane for lane in self.lanes], default=0)

    def accept(self, visitor: EntityVisitor):
        for image in self.gel_images:
            image.accept(visitor)
        for lane in self.lanes:
            lane.accept(visitor)
        visitor.visit(self)
