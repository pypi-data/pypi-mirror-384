#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QListView, QAbstractScrollArea, QWidget
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QKeyEvent

from iocbio.gel.gui.models.table_model import TableModel
from iocbio.gel.gui.views.delegates.nobackground_delegate import NoBackgroundDelegate


class GelImagesView(QListView):
    def __init__(self, model: TableModel, parent: QWidget = None):
        super().__init__(parent)
        self.setModel(model)
        model.selection_model = self.selectionModel()

        self.delegate = NoBackgroundDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.setSelectionMode(QListView.SingleSelection)
        self.setViewMode(QListView.IconMode)
        self.setSpacing(20)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)

        self.doubleClicked.connect(self.on_double_clicked)

    @Slot(QModelIndex)
    def on_double_clicked(self, index: QModelIndex):
        self.model().select_item(index.row())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Return:
            index = self.currentIndex()
            if index.isValid():
                self.model().select_item(index.row())
        return super().keyPressEvent(event)
