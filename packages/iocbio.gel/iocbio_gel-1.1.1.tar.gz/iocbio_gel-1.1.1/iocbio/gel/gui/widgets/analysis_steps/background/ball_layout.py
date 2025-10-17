#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QCheckBox, QLabel

from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.background.parameters import Parameters
from iocbio.gel.gui.widgets.mandatory_line_edit import MandatoryLineEdit


class BallLayout(Parameters):
    SCALE_TOOLTIP = (
        "It is recommended to enable scaling of the image. "
        "When enabled, the image is scaled before rolling ball is applied. "
        "This speeds up calculations and is expected to result in background estimation "
        "that follows the main features of the image."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scale_background = QCheckBox()
        self.scale_background.setChecked(True)
        self.scale_background.setToolTip(self.SCALE_TOOLTIP)
        self.scale_label = QLabel("Use scaled image: ")
        self.scale_label.setToolTip(self.SCALE_TOOLTIP)

        self.radius_x = MandatoryLineEdit()
        self.radius_x.setValidator(QIntValidator(bottom=1, parent=self))

        self._add_rows()

    def set_image(self, image: GelImage) -> None:
        text = "" if image.background_radius_x is None else str(image.background_radius_x)
        self.radius_x.setText(text)
        self.radius_x.setValidator(
            QIntValidator(bottom=1, top=image.image.final.shape[0], parent=self)
        )

        self.scale_background.setChecked(image.background_scale)

    def get_fields(self) -> dict:
        fields = super().get_fields()
        fields["background_radius_x"] = int(self.radius_x.text()) if self.radius_x.text() else None
        fields["background_scale"] = self.scale_background.isChecked()
        return fields

    def _add_rows(self):
        self.addRow("Radius: ", self.radius_x)
        self.addRow(self.scale_label, self.scale_background)
