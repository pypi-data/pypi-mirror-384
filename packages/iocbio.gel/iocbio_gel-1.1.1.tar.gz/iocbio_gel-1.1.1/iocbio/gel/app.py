#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import argparse
import keyring
import logging
import os
import sqlalchemy
import sys
import traceback

from logging.config import fileConfig
from pathlib import Path, PurePath
from time import time, sleep
from dependency_injector.wiring import Provide, inject
from PySide6.QtCore import Qt, QDir, QStandardPaths
from PySide6.QtWidgets import QApplication, QDialog, QSplashScreen
from PySide6.QtGui import QIcon, QPixmap

from iocbio.gel.application.container import Container
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.db.database_setup import DatabaseSetup
from iocbio.gel.gui.dialogs.db_selection import DbSelectionDialog
from iocbio.gel.gui.dialogs.image_source_settings.image_source_settings import (
    ImageSourceSelectionDialog,
)
from iocbio.gel.gui.widgets.warning_popup import WarningPopup
from iocbio.gel.gui.windows.main import MainWindow


def configure_logs(app_local_data):
    path = Path(app_local_data)
    path.mkdir(parents=True, exist_ok=True)
    log_path = PurePath(path, "app.log")
    logging.log_file_location = log_path

    log_config = PurePath(Path(__file__).parent, "logging.ini")
    fileConfig(log_config, disable_existing_loggers=False)


def init_data_source(
    dialog: DbSelectionDialog, setup: DatabaseSetup, client: DatabaseClient
) -> bool:
    """
    Database setup.
    Prompts user on initial setup for database connection parameters.
    Checks connection and runs migrations on every startup.
    """
    if not setup.get_connection_type() or not setup.has_connection_string():
        dialog.exec()
        if dialog.result() != QDialog.DialogCode.Accepted:
            return False
        client.start_session()
        return True

    try:
        setup.migrate_database()
    except sqlalchemy.exc.OperationalError as e:
        dialog.set_error(str(e))
        dialog.exec()
        if dialog.result() != QDialog.DialogCode.Accepted:
            return False

    client.start_session()
    return True


def init_image_source(
    dialog: ImageSourceSelectionDialog, setup: ImageSourceSetup, omero_client: OmeroClient
) -> bool:
    """
    Image source setup.
    Prompts user on initial setup for image source parameters.
    Checks connection and refreshes cache on every startup.
    """
    if not setup.get_type():
        dialog.exec()
        if dialog.result() != QDialog.DialogCode.Accepted:
            return False

    if omero_client.is_active() and not omero_client.has_session():
        try:
            omero_client.start_session()
        except (ConnectionError, ValueError) as e:
            dialog.set_error(str(e))
            dialog.exec()
            return dialog.result() == QDialog.DialogCode.Accepted

    return True


@inject
def app(
    application,
    splash: QSplashScreen,
    test_mode=False,
    event_registry: EventRegistry = Provide[Container.event_registry],
    db_setup: DatabaseSetup = Provide[Container.database_setup],
    db_selection_dialog: DbSelectionDialog = Provide[Container.db_selection_dialog],
    image_source_setup: ImageSourceSetup = Provide[Container.image_source_setup],
    image_source_selection_dialog: ImageSourceSelectionDialog = Provide[
        Container.image_source_selection_dialog
    ],
    db_client: DatabaseClient = Provide[Container.database_client],
    omero_client: OmeroClient = Provide[Container.omero_client],
    main_window: MainWindow = Provide[Container.main_window],
) -> None:
    """
    Application startup and shutdown.
    """
    if test_mode:
        return sys.exit(0)
    if not init_data_source(db_selection_dialog, db_setup, db_client):
        return
    if not init_image_source(image_source_selection_dialog, image_source_setup, omero_client):
        return

    logger = logging.getLogger(__name__)

    def on_exception(cls, exception, trace):
        import threading

        logger.error(
            f"Exception on thread {threading.current_thread().ident}: {str(exception)}",
            exc_info=True,
        )
        logger.debug("".join(traceback.format_tb(trace)))
        logger.debug(f"Is main thread: {threading.current_thread() is threading.main_thread()}")
        # Only show dialog on main thread to avoid macOS crash
        if threading.current_thread() is threading.main_thread():
            WarningPopup("Fatal error: Closing application", str(exception)).exec()
        application.closeAllWindows()

    sys.excepthook = on_exception

    main_window.show()
    splash.finish(main_window)
    event_registry.db_connected.emit()
    application.exec()

    omero_client.close_session()
    db_client.close()


def main():
    """
    Application entrypoint.
    """
    parser = argparse.ArgumentParser(description="IocBio gel tool")
    parser.add_argument("--organization", type=str, default="iocbio", help="Organization name")
    parser.add_argument("--application", type=str, default="gel", help="Application name")
    args = parser.parse_args()

    is_testing = os.getenv("TEST_APP_STARTUP_INTEGRITY", "False") == "True"

    application = QApplication(sys.argv)
    application.setOrganizationName(args.organization)
    application.setApplicationName(args.application)

    window_icon = QIcon(":/icons/gel.svg")
    application.setWindowIcon(window_icon)

    splash = QSplashScreen(QPixmap(":/icons/gel.svg"))
    splash.showMessage("Starting IOCBIO Gel", Qt.AlignBottom | Qt.AlignCenter, Qt.white)

    # Showing splashscreen requires a small hack with processing
    # events several times
    if not is_testing:
        application.processEvents()
        splash.show()
        start = time()
        while time() - start < 0.1:
            sleep(0.001)
            application.processEvents()

    app_local_data = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
    configure_logs(app_local_data)

    container = Container()

    container.config.from_dict(
        {
            "organization": args.organization,
            "application": args.application,
            "path": {
                "working_dir": os.path.normpath(os.path.join(os.getcwd())),
                "images": os.path.normpath(
                    QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
                ),
                "cache": os.path.normpath(
                    QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
                ),
                "app_local_data": app_local_data,
                "os_root": os.path.normpath(QDir.rootPath()),
                "documents": os.path.normpath(
                    QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
                ),
            },
        }
    )

    if is_testing:
        keyring.get_password = lambda x, y: None
        keyring.set_password = lambda x, y, z: None

    container.init_resources()
    container.wire(modules=[__name__])

    app(application=application, test_mode=is_testing, splash=splash)


if __name__ == "__main__":
    main()
