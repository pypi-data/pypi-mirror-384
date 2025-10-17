#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QShowEvent, QHideEvent, QAction
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QToolBar

from iocbio.gel.gui.models.gel_lanes_model import GelLanesModel
from iocbio.gel.gui.views.delegates.non_negative_double import NonNegativeDouble
from iocbio.gel.gui.views.gel_images_view import GelImagesView
from iocbio.gel.gui.views.table_view import TableView
from iocbio.gel.gui.widgets.gel_form import GelForm
from iocbio.gel.gui.widgets.gel_image_form import GelImageForm


class SingleGelWidget(QWidget):
    def __init__(
        self,
        gel_form: GelForm,
        gel_images_view: GelImagesView,
        gel_image_form: GelImageForm,
        gel_lanes_view: TableView,
        toolbar: QToolBar,
        add_gel: QAction,
    ):
        super().__init__()

        self.gel_form = gel_form
        self.toolbar = toolbar
        self.add_gel = add_gel
        self.remove_gel = self.gel_form.remove_gel

        self.add_gel.setVisible(False)
        self.remove_gel.setVisible(False)
        self.toolbar.addAction(self.add_gel)
        self.toolbar.addAction(self.remove_gel)

        gel_lanes_view.setItemDelegateForColumn(
            GelLanesModel.PROTEIN_INDEX, NonNegativeDouble(parent=gel_lanes_view)
        )

        self.layout = QVBoxLayout()

        self.layout.addWidget(gel_form)

        self.layout.addWidget(QLabel("<h2>Lanes</h2>"))
        self.layout.addWidget(gel_lanes_view)

        self.layout.addWidget(QLabel("<h2>Images</h2>"))
        images = QHBoxLayout()
        images.addWidget(gel_images_view)
        images.addWidget(gel_image_form)
        self.layout.addLayout(images)

        self.setLayout(self.layout)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.add_gel.setVisible(True)
        self.remove_gel.setVisible(True)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self.add_gel.setVisible(False)
        self.remove_gel.setVisible(False)
