from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectin_polymorphic, selectinload

import libqcanvas.database.tables as db


class DataMonolith:
    def __init__(
        self,
        courses: Sequence[db.Course],
        resources: Sequence[db.Resource],
        terms: Sequence[db.Term],
    ):
        self.courses = sorted(courses, key=lambda x: x.name)
        self.resources = self._create_resource_map(resources)
        self.terms = terms

    @staticmethod
    def _create_resource_map(resources):
        return {resource.id: resource for resource in resources}

    @staticmethod
    async def create(session: AsyncSession) -> "DataMonolith":
        eager_load_resources = [
            joinedload(db.Resource.course),
            selectin_polymorphic(db.Resource, [db.PanoptoResource]),
        ]

        query = select(db.Course).options(selectinload("*"))
        courses = (await session.scalars(query)).unique().all()
        query = select(db.Resource).options(*eager_load_resources)
        resources = (await session.scalars(query)).all()
        query = (
            select(db.Term)
            .order_by(db.Term.start_date.desc())
            .options(selectinload("*"))
        )
        terms = (await session.scalars(query)).unique().all()

        return DataMonolith(courses=courses, resources=resources, terms=terms)
