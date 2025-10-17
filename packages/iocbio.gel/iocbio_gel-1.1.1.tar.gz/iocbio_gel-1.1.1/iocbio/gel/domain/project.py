#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from sqlalchemy import Column, Integer, select, MetaData, Table, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, validates

from iocbio.gel.db.base import Base, Entity
from iocbio.gel.db.entity_visitor import EntityVisitor

metadata_obj = MetaData()

project_table = Table(
    "project",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("parent_id", Integer, ForeignKey("project.id")),
    Column("name", String),
    Column("comment", String),
)

path_table = Table(
    "project_with_path",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("path", String),
)

project_select = (
    select(project_table, path_table.c.path.label("_path"))
    .join_from(project_table, path_table, project_table.c.id == path_table.c.id)
    .subquery()
)

association_table = Table(
    "gel_to_project",
    Entity.metadata,
    Column("gel_id", ForeignKey("gel.id"), primary_key=True),
    Column("project_id", ForeignKey(project_table.c.id), primary_key=True),
)


class Project(Entity, Base):
    """
    Project for grouping gels.
    """

    __table__ = project_select

    __mapper_args__ = {"confirm_deleted_rows": False}

    gels = relationship(
        "iocbio.gel.domain.gel.Gel",
        order_by="asc(iocbio.gel.domain.gel.Gel.name)",
        secondary="gel_to_project",
        back_populates="projects",
    )
    parent = relationship("Project", remote_side=[project_select.c.id], viewonly=True)
    children: list = relationship("Project", viewonly=True)

    @property
    def descendants(self):
        stmt = select(Project).where(Project.path.like(f"{self.path}/%")).order_by(Project.path)
        return object_session(self).execute(stmt).scalars().all()

    @property
    def gels_count(self):
        return len(self.gels)

    @validates("name")
    def validate_name(self, _, name):
        if "/" in name:
            raise ValueError("Character / is not allowed in project name")
        name = name.strip()
        if len(name) == 0:
            raise ValueError("Project name can't be empty")
        return name

    @hybrid_property
    def path(self):
        return self._path

    def accept(self, visitor: EntityVisitor):
        for child in self.children:
            child.accept(visitor)
        visitor.visit(self)
