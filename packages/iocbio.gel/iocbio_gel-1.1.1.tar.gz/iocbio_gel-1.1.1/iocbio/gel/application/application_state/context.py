#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from iocbio.gel.domain.gel import Gel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.domain.measurement import Measurement


class Context:
    @classmethod
    def from_context(cls, old: "Context"):
        return cls(old.gel, old.image, old.measurement)

    def __init__(self, gel: Gel = None, image: GelImage = None, measurement: Measurement = None):
        self.gel = gel
        self.image = image
        self.measurement = measurement

    def __eq__(self, other):
        return self.__class__ == other.__class__

    @property
    def title(self):
        return self.__class__.__name__


class Projects(Context):
    pass


class Gels(Context):
    pass


class Settings(Context):
    pass


class MeasurementTypes(Context):
    @property
    def title(self):
        return "Measurement Types"


class SingleGel(Context):
    def __init__(self, gel: Gel):
        if gel is None:
            raise ValueError(
                f"Cannot create context {self.__class__.__name__} with Gel set to None"
            )
        super().__init__(gel=gel)

    def __eq__(self, other):
        return super().__eq__(other) and self.gel == other.gel

    @property
    def title(self):
        return "Gel: " + self.gel.name


class Analysis(Context):
    def __init__(self, gel: Gel, image: GelImage, measurement: Measurement = None):
        if gel is None:
            raise ValueError(
                f"Cannot create context {self.__class__.__name__} with Gel set to None"
            )
        if image is None:
            raise ValueError(
                f"Cannot create context {self.__class__.__name__} with Image set to None"
            )
        super().__init__(gel=gel, image=image, measurement=measurement)

    def __eq__(self, other):
        return super().__eq__(other) and self.gel == other.gel and self.image == other.image

    @property
    def title(self):
        return f"Gel: {self.gel.name} > Image: {self.image.image.name}"


class AnalysisRaw(Analysis):
    pass


class AnalysisAdjust(Analysis):
    pass


class AnalysisBackground(Analysis):
    pass


class AnalysisLanes(Analysis):
    pass


class AnalysisMeasurements(Analysis):
    pass
