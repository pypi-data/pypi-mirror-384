#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import keyring

from PySide6.QtCore import QSettings


class SettingsProxy:
    """
    Wrapper for interacting with the OS key-value or credentials storage.
    """

    def __init__(self, organization, application) -> None:
        self.prefix = f"{organization}.{application}"
        self.store = QSettings()

    def set(self, key, value, secure=False):
        if not secure:
            return self.store.setValue(key, value)

        keyring.set_password(self.prefix, key, value)

    def get(self, key, default=None, secure=False):
        if not secure:
            return self.store.value(key, default)

        password = keyring.get_password(self.prefix, key)
        return default if password is None else password

    def remove(self, key, secure=False):
        if not secure:
            return self.store.remove(key)
        keyring.delete_password(self.prefix, key)

    def contains(self, key, secure=False):
        if not secure:
            return self.store.contains(key)

        return keyring.get_password(self.prefix, key) is not None
