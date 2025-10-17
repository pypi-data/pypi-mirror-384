#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor


class MeasurementType(Entity, Base):
    """
    Specifies the lab specific type of the measurement.
    Typically, a specific protein.
    """

    __tablename__ = "measurement_type"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    comment = Column(Text)

    measurements = relationship("Measurement", back_populates="measurement_type")

    def accept(self, visitor: EntityVisitor):
        for measurement in self.measurements:
            measurement.accept(visitor)
        visitor.visit(self)
