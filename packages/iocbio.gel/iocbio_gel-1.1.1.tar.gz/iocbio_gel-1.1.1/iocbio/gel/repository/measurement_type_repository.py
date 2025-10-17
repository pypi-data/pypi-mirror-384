#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import select

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.db.database_client import DatabaseClient
from iocbio.gel.domain.measurement_type import MeasurementType
from iocbio.gel.repository.entity_repository import EntityRepository


class MeasurementTypeRepository(EntityRepository):
    def __init__(
        self, db: DatabaseClient, event_registry: EventRegistry, history_manager: HistoryManager
    ):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.measurement_type_updated,
            event_registry.measurement_type_added,
            event_registry.measurement_type_deleted,
        )
        self.event_registry = event_registry

    def fetch_all(self):
        stmt = select(MeasurementType).order_by(MeasurementType.name)
        return self.db.execute(stmt).scalars().all()
