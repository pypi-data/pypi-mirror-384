#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from datetime import datetime

from PySide6.QtWidgets import (
    QFormLayout,
    QWidget,
    QLabel,
    QDateTimeEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Slot, QDateTime, Qt

from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.domain.gel_image import GelImage
from iocbio.gel.application.image.image_state import ImageState


class GelImageForm(QWidget):
    STATUS = {
        ImageState.MISSING: "Missing",
        ImageState.LOADING: "Loading",
        ImageState.READY: "Ready",
    }

    def __init__(self, model: TableModel, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.model = model

        self.widget_image: QLabel() = QLabel()
        self.widget_image.setAlignment(Qt.AlignHCenter)

        self.widget_name: QLabel = QLabel()
        self.widget_status: QLabel = QLabel()
        self.widget_measurements: QLabel = QLabel()

        self.widget_taken: QDateTimeEdit = QDateTimeEdit(parent)
        self.widget_taken.setMaximumDateTime(QDateTime.currentDateTime())
        self.widget_taken.setCalendarPopup(True)
        self.widget_taken.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.button_replace: QPushButton = QPushButton("Replace image")
        self.button_delete: QPushButton = QPushButton("Delete")

        form = QFormLayout()
        form.addRow(self.widget_image)
        form.addRow(self.button_replace)
        form.addItem(QSpacerItem(0, 10))
        form.addRow("Name:", self.widget_name)
        form.addRow("Status:", self.widget_status)
        form.addRow("Image taken:", self.widget_taken)
        form.addRow("Measurements:", self.widget_measurements)
        form.addItem(QSpacerItem(0, 10, QSizePolicy.Fixed, QSizePolicy.Expanding))
        form.addRow(self.button_delete)

        self.setLayout(form)

        model.dataChanged.connect(self.on_current_changed)
        model.signals.current_changed.connect(self.on_current_changed)
        model.signals.edit_allowed_changed.connect(self.on_edit_allowed_changed)

        self.widget_taken.dateTimeChanged.connect(self.on_taken_changed)
        self.button_delete.clicked.connect(self.on_delete)
        self.button_replace.clicked.connect(self.on_replace)

        self.on_current_changed()
        self.on_edit_allowed_changed(self.model.edit_allowed)

    @Slot()
    def on_current_changed(self):
        current: GelImage = self.model.current_item

        if current is None:
            self.setVisible(False)
            return

        self.setVisible(True)

        pixmap = self.model.data(self.model.index(self.model.current_row, 0), Qt.DecorationRole)
        if pixmap is None:
            self.widget_image.clear()
        else:
            self.widget_image.setPixmap(pixmap)

        self.widget_name.setText(current.image.name)
        self.widget_status.setText(
            self.STATUS[current.image.state] if current.id is not None else ""
        )
        self.widget_measurements.setText(
            ", ".join([m.measurement_type.name for m in current.measurements])
        )

        if current.id is None:
            self.button_replace.setText("Add image")
        else:
            self.button_replace.setText("Replace image")

        taken = QDateTime(current.taken)
        if self.widget_taken.dateTime() != taken:
            self.widget_taken.setEnabled(False)
            self.widget_taken.setDateTime(taken)
            self.widget_taken.setEnabled(self.model.edit_allowed)

    @Slot(bool)
    def on_edit_allowed_changed(self, edit_allowed: bool):
        self.widget_taken.setEnabled(edit_allowed)
        self.button_delete.setEnabled(edit_allowed)
        self.button_replace.setEnabled(edit_allowed)

    @Slot(QDateTime)
    def on_taken_changed(self, taken: QDateTime):
        if not self.widget_taken.isEnabled():
            return
        date = taken.date()
        time = taken.time()
        self.model.setData(
            self.model.index(self.model.current_row, self.model.ATTR.index("taken")),
            datetime(date.year(), date.month(), date.day(), time.hour(), time.minute()),
            Qt.EditRole,
        )

    def on_delete(self):
        self.model.removeRow(self.model.current_row)

    def on_replace(self):
        self.model.replace_image(self.model.current_item)
