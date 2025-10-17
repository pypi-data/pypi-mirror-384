#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QIntValidator

from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.gui.widgets.analysis_steps.background.ball_layout import BallLayout
from iocbio.gel.gui.widgets.mandatory_line_edit import MandatoryLineEdit


class EllipsoidLayout(BallLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.radius_y = MandatoryLineEdit()
        self.radius_y.setValidator(QIntValidator(bottom=0, parent=self))

        self.addRow("Radius x: ", self.radius_x)
        self.addRow("Radius y: ", self.radius_y)
        self.addRow(self.scale_label, self.scale_background)

    def set_image(self, image: GelImage) -> None:
        super().set_image(image)

        text = "" if image.background_radius_y is None else str(image.background_radius_y)
        self.radius_y.setText(text)

        self.radius_y.setValidator(
            QIntValidator(bottom=0, top=image.image.final.shape[1], parent=self)
        )

    def get_fields(self) -> dict:
        fields = super().get_fields()
        fields["background_radius_y"] = int(self.radius_y.text()) if self.radius_y.text() else None
        return fields

    def _add_rows(self):
        pass
