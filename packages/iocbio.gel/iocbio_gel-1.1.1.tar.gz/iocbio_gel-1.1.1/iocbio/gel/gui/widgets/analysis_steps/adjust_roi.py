#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import math

import pyqtgraph as pg
from PySide6.QtCore import QPoint


class AdjustROI(pg.RectROI):
    """
    Wrapper for parent object to disable interactions.
    """

    def __init__(self, view_box, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_box = view_box
        self.is_adjustable = False

    def set_adjustable(self, is_adjustable):
        self.is_adjustable = is_adjustable
        self.removable = is_adjustable

    def mouseDragEvent(self, ev):
        if not self.is_adjustable:
            return
        mods = ev.modifiers() & ~self.mouseDragHandler.snapModifier
        if mods == self.mouseDragHandler.translateModifier:
            super().mouseDragEvent(ev)

    def checkPointMove(self, handle, pos, modifiers):
        return super().checkPointMove(handle, pos, modifiers) if self.is_adjustable else False

    def get_state(self):
        angle = self.angle()
        width, height = self.size()
        x1, y1 = self.pos()
        x2 = x1 + width * math.cos(math.radians(angle)) - height * math.sin(math.radians(angle))
        y2 = y1 + width * math.sin(math.radians(angle)) + height * math.cos(math.radians(angle))

        return x1, y1, x2, y2, width, height, angle

    def raiseContextMenu(self, ev):
        if not self.contextMenuEnabled():
            return

        menu = self.getMenu()
        vb_menu_actions = self._view_box.menu.actions()
        if vb_menu_actions != []:
            menu.addSeparator()
            menu.addActions(vb_menu_actions)

        pos = ev.screenPos()
        menu.popup(QPoint(int(pos.x()), int(pos.y())))
