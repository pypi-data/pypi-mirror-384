#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtGui import QDoubleValidator

from iocbio.gel.gui.views.delegates.selectable_row_delegate import SelectableRowDelegate


class NonNegativeDouble(SelectableRowDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if hasattr(editor, "setValidator") and callable(editor.setValidator):
            editor.setValidator(QDoubleValidator(bottom=0))
        if hasattr(editor, "setMinimum") and callable(editor.setMinimum):
            editor.setMinimum(0)
        return editor
