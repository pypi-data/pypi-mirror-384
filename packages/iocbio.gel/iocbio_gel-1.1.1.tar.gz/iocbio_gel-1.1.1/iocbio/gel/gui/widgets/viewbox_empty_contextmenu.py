#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import pyqtgraph as pg

from pyqtgraph.GraphicsScene import exportDialog

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


class ViewBoxEmptyContextMenu(pg.ViewBox):
    def __init__(
        self,
        parent=None,
        border=None,
        lockAspect=False,
        enableMouse=True,
        invertY=False,
        enableMenu=True,
        name=None,
    ):
        super().__init__(parent, border, lockAspect, enableMouse, invertY, enableMenu, name)
        self.menu = QMenu()
        self.accepted_item = None
        self.export_dialog = None

    def raiseContextMenu(self, event):
        if not self.menuEnabled():
            return

        self.accepted_item = event.acceptedItem
        menu = self.getMenu(event)
        pos = event.screenPos()
        menu.popup(QPoint(pos.x(), pos.y()))

    def show_export(self, scene):
        if self.export_dialog is None:
            self.export_dialog = exportDialog.ExportDialog(scene)
        self.export_dialog.show(self.accepted_item)

    def add_view_all_action(self, parent, obj, action=None):
        view_all = QAction("View All", parent, obj)
        if action is None:
            view_all.triggered.connect(lambda: self.autoRange(padding=0))
        else:
            view_all.triggered.connect(action)
        self.menu.addAction(view_all)

    def add_export_view_action(self, parent, obj):
        export_view = QAction("Export view", parent, obj)
        export_view.triggered.connect(lambda x: self.show_export(obj.getPlotItem().scene()))
        self.menu.addAction(export_view)
