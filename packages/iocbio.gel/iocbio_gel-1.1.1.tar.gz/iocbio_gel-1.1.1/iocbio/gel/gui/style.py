#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QSize
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

PREVIEW_ICON_SIZE = QSize(96, 96)
ICON_SIZE = QSize(16, 16)
ICON_COLOR = QApplication.palette().color(QPalette.Normal, QPalette.Dark)
SELECTED_GEL_BACKGROUND = QApplication.palette().color(QPalette.Inactive, QPalette.Midlight)
