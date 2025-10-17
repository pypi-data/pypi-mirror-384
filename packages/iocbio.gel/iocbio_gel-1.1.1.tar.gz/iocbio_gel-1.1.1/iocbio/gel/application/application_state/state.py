#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, SignalInstance

from iocbio.gel.application.application_state.context import Context, Gels
from iocbio.gel.application.application_state.mode import ApplicationMode
from iocbio.gel.domain.project import Project


class ApplicationState(QObject):
    """
    Store application state and notify on change.
    """

    mode_changed: SignalInstance = Signal(ApplicationMode)
    context_changed: SignalInstance = Signal(Context)
    project_changed: SignalInstance = Signal(Project)

    def __init__(self):
        super().__init__()
        self._mode: ApplicationMode = ApplicationMode.VIEWING
        self._context: Context = Gels()
        self._project: Optional[Project] = None

    def _get_mode(self):
        return self._mode

    def _set_mode(self, mode: ApplicationMode):
        self._set("mode", mode)

    def _get_context(self):
        return self._context

    def _set_context(self, context: Context):
        self._set("context", context)

    def _get_project(self):
        return self._project

    def _set_project(self, project: Project):
        self._set("project", project)

    def _set(self, key: str, value):
        if self.__getattribute__(f"_{key}") != value:
            self.__setattr__(f"_{key}", value)
            self.__getattribute__(f"{key}_changed").emit(value)

    mode = Property(ApplicationMode, _get_mode, _set_mode, notify=mode_changed)
    context = Property(Context, _get_context, _set_context, notify=context_changed)
    project = Property(Context, _get_project, _set_project, notify=project_changed)
