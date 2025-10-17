#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QFormLayout

from iocbio.gel.domain.gel_image import GelImage


class Parameters(QFormLayout):
    def set_image(self, image: GelImage) -> None:
        pass

    def get_fields(self) -> dict:
        return {}
