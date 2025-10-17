#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from PySide6.QtCore import QObject, Slot, SignalInstance, Signal, QItemSelectionModel, QModelIndex

from iocbio.gel.db.base import Entity


class Signals(QObject):
    # Emitted when currently highlighted item is changed in the main view
    current_changed: SignalInstance = Signal()
    # Emitted when editing of the current is either allowed or disallowed
    edit_allowed_changed: SignalInstance = Signal(bool)
    # Emitted when adding of new element is allowed or disallowed
    add_allowed_changed: SignalInstance = Signal()
    # Emitted when removal of the current is either allowed or disallowed
    remove_allowed_changed: SignalInstance = Signal()


class TrackingModel:
    """
    Abstract model extension that tracks its current item and assists with the item selection,
    addition, and removal.
    """

    def __init__(self):
        self._current_item: Entity = None
        self._current_row: int = -1
        self.signals = Signals()
        self._selection_model: QItemSelectionModel = None
        self._edit_allowed = False

    @property
    def add_allowed(self):
        return self.edit_allowed

    @property
    def current_item(self):
        return self._current_item

    @property
    def current_row(self):
        return self._current_row

    @property
    def edit_allowed(self):
        return self._edit_allowed

    @property
    def selection_model(self):
        return self._selection_model

    @property
    def remove_allowed(self):
        return self.edit_allowed and self.current_item is not None

    @current_item.setter
    def current_item(self, current_item):
        self._current_item = current_item

    @current_row.setter
    def current_row(self, current_row):
        self._current_row = current_row

    @edit_allowed.setter
    def edit_allowed(self, edit_allowed):
        self._edit_allowed = edit_allowed

    @selection_model.setter
    def selection_model(self, selection_model: QItemSelectionModel):
        """
        Set the model to follow the selection of some specific view allowing other views to follow that selection
        as well.
        """
        if self._selection_model is not None and selection_model is not None:
            raise RuntimeError(f"Only one selection model can be set for {__name__}")
        if self._selection_model is not None:
            self._selection_model.currentChanged.disconnect(self.on_current_changed)
        if selection_model is not None:
            selection_model.currentChanged.connect(self.on_current_changed)
        self._selection_model = selection_model

    @Slot(QModelIndex)
    def on_current_changed(self, current_index: QModelIndex):
        raise NotImplementedError()

    def select_item(self, row: int):
        raise NotImplementedError()

    def add_new(self, explicit: bool = False):
        raise NotImplementedError()

    def remove_current(self):
        raise NotImplementedError()
