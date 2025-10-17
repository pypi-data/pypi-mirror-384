#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import func, select

from iocbio.gel.application.event_registry import EventRegistry
from iocbio.gel.command.history_manager import HistoryManager
from iocbio.gel.domain.gel_lane import GelLane
from iocbio.gel.repository.entity_repository import EntityRepository


class GelLaneRepository(EntityRepository):
    def __init__(self, db, event_registry: EventRegistry, history_manager: HistoryManager):
        super().__init__(
            db,
            history_manager,
            event_registry,
            event_registry.gel_lane_updated,
            event_registry.gel_lane_added,
            event_registry.gel_lane_deleted,
        )

    def get_count_by_gel_id(self, gel_id):
        stmt = select(func.count()).select_from(GelLane).where(GelLane.gel_id == gel_id)

        return self.db.execute(stmt).scalars().one()

    def fetch_by_gel_id(self, gel_id):
        stmt = select(GelLane).where(GelLane.gel_id == gel_id).order_by(GelLane.lane)

        return self.db.execute(stmt).scalars().all()

    def fetch_lane_list_by_gel_id(self, gel_id):
        stmt = select(GelLane.lane).where(GelLane.gel_id == gel_id).order_by(GelLane.lane)

        return [lane for lane in self.db.execute(stmt).scalars()]
