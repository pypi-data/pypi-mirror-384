#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


"""Wiring for services."""
from dependency_injector import containers, providers
from PySide6.QtWidgets import QToolBar

from iocbio.gel.application.application_state.state import ApplicationState
from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.application.image.image_source_setup import ImageSourceSetup
from iocbio.gel.application.image.omero_client import OmeroClient
from iocbio.gel.application.image.processing_cache import ProcessingCache
from iocbio.gel.application.image.repository_backend_local import ImageRepositoryBackendLocal
from iocbio.gel.application.image.repository_backend_omero import ImageRepositoryBackendOmero
from iocbio.gel.application.settings_proxy import SettingsProxy
from iocbio.gel.application.thread.thread_pool import ThreadPool
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.db.database_setup import DatabaseSetup
from iocbio.gel.domain.xls_writer import XlsWriter
from iocbio.gel.gui.contexts.analysis import AnalysisWidget
from iocbio.gel.gui.contexts.gels import GelsWidget
from iocbio.gel.gui.contexts.measurement_types import MeasurementTypesWidget
from iocbio.gel.gui.contexts.projects import ProjectsWidget
from iocbio.gel.gui.contexts.settings import SettingsWidget
from iocbio.gel.gui.contexts.single_gel import SingleGelWidget
from iocbio.gel.gui.dialogs.database_connection_settings.db_selection_form import DbSelectionForm
from iocbio.gel.gui.dialogs.database_connection_settings.sqlite_connection_settings import (
    SQLiteConnectionSettings,
)
from iocbio.gel.gui.dialogs.db_selection import DbSelectionDialog
from iocbio.gel.gui.dialogs.image_source_settings.image_source_form import ImageSourceForm
from iocbio.gel.gui.dialogs.image_source_settings.image_source_settings import (
    ImageSourceSelectionDialog,
)
from iocbio.gel.gui.dialogs.select_image_factory import SelectImageFactory
from iocbio.gel.gui.dialogs.select_image_local import SelectImageLocal
from iocbio.gel.gui.dialogs.select_image_omero import SelectImageOmero
from iocbio.gel.gui.models.gel_images_model import GelImagesModel
from iocbio.gel.gui.models.gel_lanes_model import GelLanesModel
from iocbio.gel.gui.models.gels_model import GelsModel
from iocbio.gel.gui.models.measurement_lanes_model import MeasurementLanesModel
from iocbio.gel.gui.models.measurement_types_model import MeasurementTypesModel
from iocbio.gel.gui.models.measurements_model import MeasurementsModel
from iocbio.gel.gui.models.projects_tree_model import ProjectsTreeModel
from iocbio.gel.gui.models.projects_gels_model import ProjectsGelsModel
from iocbio.gel.gui.models.proxy_table_model import ProxyTableModel
from iocbio.gel.gui.views.delegates.multiselect_delegate import MultiselectDelegate
from iocbio.gel.gui.views.gel_images_view import GelImagesView
from iocbio.gel.gui.views.table_view import TableView
from iocbio.gel.gui.views.tree_view import TreeView
from iocbio.gel.gui.widgets.analysis_steps.active_lanes import ActiveLanes
from iocbio.gel.gui.widgets.analysis_steps.adjust import Adjust
from iocbio.gel.gui.widgets.analysis_steps.background_subtraction import BackgroundSubtraction
from iocbio.gel.gui.widgets.analysis_steps.intensity.lane_intensity_plot import LaneIntensityPlot
from iocbio.gel.gui.widgets.analysis_steps.intensity.lane_plot_list import LanePlotList
from iocbio.gel.gui.widgets.analysis_steps.intensity.measurement_intensity_plot import (
    MeasurementIntensityPlot,
)
from iocbio.gel.gui.widgets.analysis_steps.intensity.measurement_plot_list import (
    MeasurementPlotList,
)
from iocbio.gel.gui.widgets.analysis_steps.passive_lanes import PassiveLanes
from iocbio.gel.gui.widgets.analysis_steps.raw import Raw
from iocbio.gel.gui.widgets.gel_form import GelForm
from iocbio.gel.gui.widgets.gel_image_form import GelImageForm
from iocbio.gel.gui.widgets.gel_measurements import GelMeasurements
from iocbio.gel.gui.widgets.sidebar import Sidebar
from iocbio.gel.gui.widgets.status_bar import StatusBar
from iocbio.gel.gui.widgets.toolbars.add_gel import AddGel
from iocbio.gel.gui.widgets.toolbars.main import MainToolbar
from iocbio.gel.gui.widgets.multiple_project_selection import MultipleProjectSelection
from iocbio.gel.gui.widgets.project_selection import ProjectSelection
from iocbio.gel.gui.windows.main import MainWindow
from iocbio.gel.repository.export_repository import ExportRepository
from iocbio.gel.repository.gel_image_lane_repository import GelImageLaneRepository
from iocbio.gel.repository.gel_image_repository import GelImageRepository
from iocbio.gel.repository.gel_lane_repository import GelLaneRepository
from iocbio.gel.repository.gel_repository import GelRepository
from iocbio.gel.repository.image_repository import ImageRepository
from iocbio.gel.repository.measurement_lane_repository import MeasurementLaneRepository
from iocbio.gel.repository.measurement_repository import MeasurementRepository
from iocbio.gel.repository.measurement_type_repository import MeasurementTypeRepository
from iocbio.gel.repository.project_repository import ProjectRepository


class Container(containers.DeclarativeContainer):
    """
    Container for specifying dependencies.
    """

    config = providers.Configuration()
    settings = providers.Singleton(
        SettingsProxy, organization=config.organization, application=config.application
    )
    event_registry = providers.Singleton(EventRegistry)
    application_state = providers.Singleton(ApplicationState)
    history_manager = providers.Singleton(
        HistoryManager, event_registry=event_registry, application_state=application_state
    )
    thread_pool = providers.Singleton(ThreadPool, event_registry=event_registry)

    # Database

    database_setup = providers.Singleton(DatabaseSetup, settings=settings)

    database_client = providers.Singleton(DatabaseClient, db_setup=database_setup)

    image_source_setup = providers.Singleton(
        ImageSourceSetup, default_local_directory=config.path.images, settings=settings
    )

    omero_client = providers.Singleton(
        OmeroClient,
        image_source_setup=image_source_setup,
        db_client=database_client,
        cache_path=config.path.cache,
    )

    # Image

    processing_cache = providers.Factory(
        ProcessingCache,
        cache_path=config.path.cache,
    )

    image_repository_backend_local = providers.Singleton(
        ImageRepositoryBackendLocal, image_source_setup=image_source_setup
    )

    image_repository_backend_omero = providers.Singleton(
        ImageRepositoryBackendOmero,
        omero_client=omero_client,
        thread_pool=thread_pool,
        event_registry=event_registry,
    )

    # Repositories

    project_repository = providers.Singleton(
        ProjectRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    gel_repository = providers.Singleton(
        GelRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    measurement_lane_repository = providers.Singleton(
        MeasurementLaneRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    measurement_repository = providers.Singleton(
        MeasurementRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
        measurement_lane_repository=measurement_lane_repository,
    )

    measurement_type_repository = providers.Singleton(
        MeasurementTypeRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    gel_lane_repository = providers.Singleton(
        GelLaneRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    gel_image_lane_repository = providers.Singleton(
        GelImageLaneRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
    )

    gel_image_repository = providers.Singleton(
        GelImageRepository,
        db=database_client,
        event_registry=event_registry,
        history_manager=history_manager,
        image_lane_repository=gel_image_lane_repository,
    )

    image_repository = providers.Singleton(
        ImageRepository,
        gel_image_repository=gel_image_repository,
        image_source_setup=image_source_setup,
        image_repository_backend_local=image_repository_backend_local,
        image_repository_backend_omero=image_repository_backend_omero,
        event_registry=event_registry,
        processing_cache=processing_cache,
        thread_pool=thread_pool,
    )

    export_repository = providers.Factory(
        ExportRepository, db=database_client, application_state=application_state
    )

    xls_writer = providers.Factory(XlsWriter, repository=export_repository)

    # GUI

    sql_lite_settings_dialog = providers.Factory(
        SQLiteConnectionSettings,
        db_setup=database_setup,
        data_directory=config.path.working_dir,
    )

    add_gel = providers.Factory(
        AddGel,
        event_registry=event_registry,
        application_state=application_state,
        gel_repository=gel_repository,
    )

    context_toolbar = providers.Singleton(QToolBar)

    tree_view = providers.Factory(TreeView, application_state=application_state)

    projects_gels_model = providers.Factory(
        ProjectsGelsModel,
        project_repository=project_repository,
        gel_repository=gel_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    shared_projects_model = providers.Singleton(
        ProjectsTreeModel,
        repository=project_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    multiple_project_selection = providers.Factory(
        MultipleProjectSelection,
        model=shared_projects_model,
    )

    project_selection_delegate = providers.Factory(
        MultiselectDelegate,
        select_provider=multiple_project_selection.provider,
    )

    project_selection = providers.Factory(
        ProjectSelection,
        model=shared_projects_model,
        event_registry=event_registry,
        application_state=application_state,
        settings=settings,
    )

    main_toolbar = providers.Singleton(
        MainToolbar,
        event_registry=event_registry,
        history_manager=history_manager,
        application_state=application_state,
        context_toolbar=context_toolbar,
    )

    db_selection_form = providers.Factory(
        DbSelectionForm,
        db_setup=database_setup,
        sql_lite_settings=sql_lite_settings_dialog,
    )

    db_selection_dialog = providers.Factory(
        DbSelectionDialog,
        form_provider=db_selection_form.provider,
    )

    image_source_form = providers.Factory(
        ImageSourceForm,
        image_source_setup=image_source_setup,
        omero_client=omero_client,
    )

    image_source_selection_dialog = providers.Factory(
        ImageSourceSelectionDialog,
        form_provider=image_source_form.provider,
    )

    lane_intensity_plot = providers.Factory(LaneIntensityPlot, application_state=application_state)

    measurement_intensity_plot = providers.Factory(
        MeasurementIntensityPlot, application_state=application_state
    )

    active_lane_intensity = providers.Factory(
        MeasurementPlotList,
        event_registry=event_registry,
        application_state=application_state,
        plot_provider=measurement_intensity_plot.provider,
        measurement_repository=measurement_repository,
        measurement_lane_repository=measurement_lane_repository,
        toolbar=context_toolbar,
    )

    passive_lane_intensity = providers.Factory(
        LanePlotList,
        event_registry=event_registry,
        application_state=application_state,
        plot_provider=lane_intensity_plot.provider,
        repository=gel_image_lane_repository,
    )

    raw_image = providers.Factory(Raw, application_state=application_state)

    adjust_image = providers.Factory(
        Adjust,
        gel_image_repository=gel_image_repository,
        image_repository=image_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    passive_lanes = providers.Factory(
        PassiveLanes,
        event_registry=event_registry,
        gel_image_lane_repository=gel_image_lane_repository,
        settings=settings,
        application_state=application_state,
    )

    active_lanes = providers.Factory(
        ActiveLanes,
        event_registry=event_registry,
        gel_image_lane_repository=gel_image_lane_repository,
        gel_image_repository=gel_image_repository,
        settings=settings,
        application_state=application_state,
        toolbar=context_toolbar,
    )

    background_subtraction = providers.Factory(
        BackgroundSubtraction,
        event_registry=event_registry,
        gel_image_repository=gel_image_repository,
        image_repository=image_repository,
        settings=settings,
        application_state=application_state,
    )

    select_image_factory = providers.Factory(
        SelectImageFactory,
        providers.Factory(
            SelectImageLocal, image_source_setup=image_source_setup, settings=settings
        ).provider,
        providers.Factory(
            SelectImageOmero,
            event_registry=event_registry,
            omero_client=omero_client,
            thread_pool=thread_pool,
        ).provider,
        image_source_setup=image_source_setup,
    )

    gels_model = providers.Factory(
        GelsModel,
        gel_repository=gel_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    gels_context = providers.Factory(
        GelsWidget,
        application_state=application_state,
        gels_model=gels_model,
        projects_model=shared_projects_model,
        project_selection_delegate=project_selection_delegate.provider,
        toolbar=context_toolbar,
        add_gel=add_gel,
        settings=settings,
    )

    sidebar = providers.Factory(
        Sidebar,
        event_registry=event_registry,
        application_state=application_state,
        project_selection=project_selection,
        model=projects_gels_model,
        writer=xls_writer,
        documents_path=config.path.documents,
        settings=settings,
    )

    measurements_model = providers.Factory(
        MeasurementsModel,
        measurement_repository=measurement_repository,
        measurement_type_repository=measurement_type_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    measurement_lanes_model = providers.Factory(
        MeasurementLanesModel,
        measurement_lane_repository=measurement_lane_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    measurement_lanes_view = providers.Factory(
        TableView,
        model=providers.Factory(ProxyTableModel, model=measurement_lanes_model),
        settings=settings,
    )

    measurement_types_model = providers.Factory(
        MeasurementTypesModel,
        measurement_type_repository=measurement_type_repository,
        measurement_repository=measurement_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    projects_context = providers.Factory(
        ProjectsWidget,
        application_state=application_state,
        settings=settings,
        model=shared_projects_model,
        view_provider=tree_view.provider,
        toolbar=context_toolbar,
    )

    measurement_types_context = providers.Factory(
        MeasurementTypesWidget,
        model=measurement_types_model,
        toolbar=context_toolbar,
        settings=settings,
    )

    gel_measurements = providers.Factory(
        GelMeasurements,
        application_state=application_state,
        event_registry=event_registry,
        measurements_model=measurements_model,
        toolbar=context_toolbar,
        settings=settings,
    )

    gel_images_model = providers.Singleton(
        GelImagesModel,
        gel_image_repository=gel_image_repository,
        image_repository=image_repository,
        dialog_factory=select_image_factory,
        event_registry=event_registry,
        application_state=application_state,
    )

    gel_images_view = providers.Factory(GelImagesView, model=gel_images_model)

    gel_image_form = providers.Factory(GelImageForm, model=gel_images_model)

    gel_form = providers.Factory(
        GelForm,
        gel_repository=gel_repository,
        event_registry=event_registry,
        application_state=application_state,
        project_selection=multiple_project_selection,
    )

    gel_lanes_model = providers.Factory(
        GelLanesModel,
        gel_lane_repository=gel_lane_repository,
        event_registry=event_registry,
        application_state=application_state,
    )

    gel_lanes_view = providers.Factory(
        TableView,
        model=providers.Factory(ProxyTableModel, model=gel_lanes_model),
        settings=settings,
    )

    single_gel_context = providers.Factory(
        SingleGelWidget,
        gel_form=gel_form,
        gel_images_view=gel_images_view,
        gel_image_form=gel_image_form,
        gel_lanes_view=gel_lanes_view,
        toolbar=context_toolbar,
        add_gel=add_gel,
    )

    settings_context = providers.Factory(
        SettingsWidget,
        db_client=database_client,
        db_setup=database_setup,
        image_source_setup=image_source_setup,
        event_registry=event_registry,
        image_form_provider=image_source_form.provider,
        db_form_provider=db_selection_form.provider,
        logs_folder=config.path.app_local_data,
        processing_cache=processing_cache,
        thread_pool=thread_pool,
    )

    status_bar = providers.Factory(
        StatusBar,
        event_registry=event_registry,
    )

    analysis_context = providers.Factory(
        AnalysisWidget,
        gel_measurements=gel_measurements,
        raw_image=raw_image,
        adjust_image=adjust_image,
        active_lanes=active_lanes,
        passive_lanes=passive_lanes,
        background_subtraction=background_subtraction,
        active_lane_intensity=active_lane_intensity,
        passive_lane_intensity=passive_lane_intensity,
        measurement_lanes_view=measurement_lanes_view,
        event_registry=event_registry,
        settings=settings,
        application_state=application_state,
    )

    main_window = providers.Factory(
        MainWindow,
        application_state=application_state,
        history_manager=history_manager,
        settings=settings,
        toolbar=main_toolbar,
        statusbar=status_bar,
        sidebar=sidebar,
        analysis_context=analysis_context,
        gels_context=gels_context,
        single_gel_context=single_gel_context,
        measurement_types_context=measurement_types_context,
        settings_context=settings_context,
        projects_context=projects_context,
    )
