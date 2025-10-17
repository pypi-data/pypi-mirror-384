#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import json
import numpy as np

from sqlalchemy import Column, Integer, Text, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.domain.curved_lane_region import CurvedLaneRegion as LaneRegion


class GelImageLane(Entity, Base):
    """
    Entity holding the data for user-placed lanes on the gel image.
    """

    INITIAL_ZERO_LINE_PERCENTILE = 0.1

    __tablename__ = "image_lane"
    __table_args__ = (
        ForeignKeyConstraint(["image_id", "gel_id"], ["image.id", "image.gel_id"]),
        ForeignKeyConstraint(["gel_lane_id", "gel_id"], ["gel_lane.id", "gel_lane.gel_id"]),
    )

    id = Column(Integer, primary_key=True)
    gel_id = Column(Integer, nullable=False)
    gel_lane_id = Column(Integer, nullable=False)
    image_id = Column(Integer, nullable=False)
    region = Column(Text)
    zero_line_points = Column(Text)

    gel_image = relationship(
        "GelImage", back_populates="lanes", uselist=False, overlaps="gel_image_lanes"
    )
    gel_lane: GelLane = relationship(
        "GelLane", back_populates="gel_image_lanes", uselist=False, overlaps="gel_image,lanes"
    )
    measurement_lanes = relationship("MeasurementLane", back_populates="image_lane")

    @property
    def width(self) -> int:
        return self.get_region().width

    def get_region(self) -> LaneRegion:
        return LaneRegion.deserialize(self.region)

    def set_region(self, lane_region: LaneRegion):
        self.region = lane_region.serialize()

    def get_zero_line(self) -> list:
        if self.zero_line_points:
            return list(json.loads(self.zero_line_points))
        # make default one
        v = np.percentile(self.calculate_intensities(), GelImageLane.INITIAL_ZERO_LINE_PERCENTILE)
        x0, x1 = self.get_region_range()
        return [[x0, v], [x1, v]]

    def set_zero_line(self, region: list):
        self.zero_line_points = json.dumps(region)

    def accept(self, visitor: EntityVisitor):
        for lane in self.measurement_lanes:
            lane.accept(visitor)
        visitor.visit(self)

    def get_region_range(self):
        """Get minimal and maximal coordinate for region selection"""
        image = self.gel_image.get_plot_data()
        return 0, image.shape[0] - 1

    def calculate_intensities(self):
        lane_region: LaneRegion = self.get_region()
        image = self.gel_image.get_plot_data()
        return lane_region.calculate_intensities(image)

    def calculate_area(self, mn: float = None, mx: float = None):
        """
        Finds the area between integration bounds and above the zero-line.
        """
        points = np.array(self.get_zero_line())
        intensities = np.array(self.calculate_intensities())
        min_limit, max_limit = self.get_region_range()
        if mn is not None and mn > min_limit:
            min_limit = mn
        if mx is not None and mx < max_limit:
            max_limit = mx

        xx = np.arange(intensities.shape[0])
        intensities -= np.interp(xx, points[:, 0], points[:, 1])
        v0, v1 = np.interp([min_limit, max_limit], xx, intensities)
        # slice arrays
        i0, i1 = int(min_limit), int(np.ceil(max_limit))
        xx = np.hstack(([min_limit], xx[i0:i1], [max_limit]))
        intensities = np.hstack(([v0], intensities[i0:i1], [v1]))
        dx = xx[1:] - xx[:-1]
        intensities = 0.5 * (intensities[1:] + intensities[:-1])
        return np.sum(dx * intensities)

    def get_updated_measurements(self):
        updates = []
        measurement_lanes = self.measurement_lanes
        min_limit, max_limit = self.get_region_range()
        for lane in measurement_lanes:
            if lane.min is not None:
                min_limit = lane.min
            else:
                min_limit = min_limit
            if lane.max is not None:
                max_limit = lane.max
            else:
                max_limit = max_limit
            lane.value = self.calculate_area(min_limit, max_limit)
            updates.append(lane)
        return updates
