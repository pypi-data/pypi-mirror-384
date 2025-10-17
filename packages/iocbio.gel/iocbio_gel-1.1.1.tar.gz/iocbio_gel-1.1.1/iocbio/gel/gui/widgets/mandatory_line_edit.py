#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtWidgets import QLineEdit


class MandatoryLineEdit(QLineEdit):
    WARNING_STYLE = (
        "QLineEdit:enabled{ border: 1px solid red; padding-top: 1px; padding-bottom: 1px; }"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_style = self.styleSheet()
        self._on_editing_finished()
        self.textChanged.connect(self._on_editing_finished)

    def _on_editing_finished(self):
        style = self.WARNING_STYLE if len(self.text()) == 0 else self.default_style
        self.setStyleSheet(style)
