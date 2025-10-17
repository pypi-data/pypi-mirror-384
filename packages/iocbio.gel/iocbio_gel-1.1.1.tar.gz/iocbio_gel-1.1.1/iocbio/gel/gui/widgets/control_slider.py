#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QSlider, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QLabel


class ControlSlider(QWidget):
    sigValueChanged = Signal(np.float32)

    def __init__(self, label, position, min_position, max_position, spin_box_size, step=1):
        super().__init__()

        self.position = position
        self.step = step

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(min_position / self.step, max_position / self.step)
        self.slider.setValue(position / self.step)

        self.valueSpinBox = QDoubleSpinBox()
        self.valueSpinBox.setFixedWidth(spin_box_size)
        self.valueSpinBox.setRange(min_position, max_position)
        self.valueSpinBox.setValue(position)
        self.valueSpinBox.setSingleStep(step)

        self.slider.valueChanged.connect(lambda x: self.valueSpinBox.setValue(self.step * x))
        self.valueSpinBox.valueChanged.connect(lambda x: self.slider.setValue(x / self.step))
        self.slider.valueChanged.connect(self.valueChanged)

        layout_slider = QHBoxLayout()
        layout_slider.addWidget(self.slider)
        layout_slider.addWidget(self.valueSpinBox)

        mainlayout = QVBoxLayout()
        mainlayout.addWidget(QLabel(label))
        mainlayout.addLayout(layout_slider)
        mainlayout.addStretch()
        self.setLayout(mainlayout)

    def valueChanged(self):
        self.position = self.slider.value()
        self.sigValueChanged.emit(self.position * self.step)

    def set_position(self, position):
        self.slider.setValue(position / self.step)
