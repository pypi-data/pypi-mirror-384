#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional

from PySide6.QtWidgets import QGroupBox, QFormLayout, QComboBox

from iocbio.gel.application.image.background_method import BackgroundMethod
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.background.ball_layout import BallLayout
from iocbio.gel.gui.widgets.analysis_steps.background.ellipsoid_layout import EllipsoidLayout
from iocbio.gel.gui.widgets.analysis_steps.background.parameters import Parameters


class BgSubtractionBox(QGroupBox):
    """
    Widget for selecting image background subtraction method.
    """

    METHOD_PARAMETERS = {
        BackgroundMethod.NONE: Parameters,
        BackgroundMethod.FLAT: Parameters,
        BackgroundMethod.BALL: BallLayout,
        BackgroundMethod.ELLIPSOID: EllipsoidLayout,
    }

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.image: Optional[GelImage] = None

        self.method_selection = QComboBox()
        self.method_selection.addItems(BackgroundMethod.list())
        self.method_selection.currentTextChanged.connect(self.on_method_changed)

        self.method_parameters = Parameters()

        self.parent_layout = QFormLayout()
        self.parent_layout.addRow("Method:", self.method_selection)
        self.parent_layout.addRow(self.method_parameters)

        self.setLayout(self.parent_layout)

    def on_method_changed(self, method):
        """
        Change the visible parameter fields when the subtraction method is changed.
        """
        child = self.findChild(Parameters)
        if child is not None:
            self.parent_layout.removeRow(1)

        self.method_parameters = self.METHOD_PARAMETERS[method]()
        self.method_parameters.set_image(self.image)
        self.parent_layout.insertRow(1, self.method_parameters)

    def load_to_image(self, image: GelImage):
        image.background_method = self.method_selection.currentText()

        fields = self.method_parameters.get_fields()
        for key, value in fields.items():
            setattr(image, key, value)

    def load_from_image(self, image: GelImage):
        self.image = image

        method = "none" if not image.background_method else image.background_method

        if self.method_selection.currentText() != method:
            self.method_selection.setCurrentText(method)
        else:
            self.method_parameters.set_image(self.image)
