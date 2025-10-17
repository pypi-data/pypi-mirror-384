#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import json
from typing import Optional

import numpy as np
from sqlalchemy import Column, Integer, DateTime, Text, Float, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship

from iocbio.gel.application.image.image import Image
from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor


class GelImage(Entity, Base):
    """
    Entity holding the gel image and its processing parameters.
    """

    __tablename__ = "image"

    id = Column(Integer, primary_key=True)
    gel_id = Column(Integer, ForeignKey("gel.id"))
    original_file = Column(Text)
    omero_id = Column(Integer)
    hash = Column(Text)
    taken = Column(DateTime, default=func.now())
    region = Column(Text)
    rotation = Column(Float)
    background_subtraction = Column(Text)
    background_is_dark = Column(Boolean, default=False)
    sync_lane_widths = Column(Boolean, default=False)
    colormap_min = Column(Float)
    colormap_max = Column(Float)

    gel = relationship("Gel", back_populates="gel_images", uselist=False)
    lanes = relationship("GelImageLane", back_populates="gel_image")
    measurements = relationship("Measurement", back_populates="image")

    @staticmethod
    def serialize_region(x1, y1, x2, y2, width, height):
        """
        Store region as string since it is not used on the database side.
        """
        return f"{x1};{y1};{x2};{y2};{width};{height}"

    def __init__(self, *args, **kwargs):
        super(GelImage, self).__init__(*args, **kwargs)
        self.image = Image()

    @property
    def lanes_count(self):
        return len(self.lanes)

    @property
    def background_method(self) -> str:
        return self._get_bg_as_dict().get("method", "none")

    @property
    def background_scale(self) -> bool:
        value = self._get_bg_as_dict().get("scale")
        return True if value is None else value

    @property
    def background_radius_x(self) -> Optional[int]:
        value = self._get_bg_as_dict().get("radius_x")
        return value if value is None else int(value)

    @property
    def background_radius_y(self) -> Optional[int]:
        value = self._get_bg_as_dict().get("radius_y")
        return value if value is None else int(value)

    @background_method.setter
    def background_method(self, value: Optional[str]):
        bg = self._get_bg_as_dict()
        bg["method"] = "none" if value is None else str(value)
        self.background_subtraction = json.dumps(bg)

    @background_scale.setter
    def background_scale(self, value: Optional[bool]):
        bg = self._get_bg_as_dict()
        bg["scale"] = False if value is None else value
        self.background_subtraction = json.dumps(bg)

    @background_radius_x.setter
    def background_radius_x(self, value: Optional[int]):
        bg = self._get_bg_as_dict()
        if value is not None:
            bg["radius_x"] = value
        elif "radius_x" in bg:
            del bg["radius_x"]
        self.background_subtraction = json.dumps(bg)

    @background_radius_y.setter
    def background_radius_y(self, value: Optional[int]):
        bg = self._get_bg_as_dict()
        if value is not None:
            bg["radius_y"] = value
        elif "radius_y" in bg:
            del bg["radius_y"]
        self.background_subtraction = json.dumps(bg)

    def clear(self):
        self.omero_id = None
        self.original_file = None

    def deserialize_region(self):
        x1, y1, x2, y2, width, height = list(map(lambda s: float(s), self.region.split(";")))
        return x1, y1, x2, y2, width, height

    def get_plot_data(self):
        """
        Signal is measured from the bottom of the plot.
        """
        image = self.image.final
        if self.background_is_dark:
            return image
        return np.max(image) - image

    def accept(self, visitor: EntityVisitor):
        for lane in self.lanes:
            lane.accept(visitor)
        for measurement in self.measurements:
            measurement.accept(visitor)
        visitor.visit(self)

    def _get_bg_as_dict(self):
        if self.background_subtraction is None or not self.background_subtraction.strip():
            return {}
        try:
            return dict(json.loads(self.background_subtraction))
        except json.JSONDecodeError:
            message = (
                f"Error loading background information for image {self.image.name} from the database. "
                f"Please correct the field 'background_subtraction' for the record with ID={self.id} in "
                "table 'image' directly in the database and then try to open it here again."
            )
            raise ValueError(message)
