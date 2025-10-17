import logging
from asyncio import TaskGroup
from datetime import datetime

from libqcanvas_clients.canvas import CanvasClient
from sqlalchemy.ext.asyncio import AsyncSession

import libqcanvas.database.tables as db
import libqcanvas.gql_queries as gql
from libqcanvas.gql_queries import Module, ModuleItem, Page, ShallowCourse
from libqcanvas.net.canvas.course_bundle import CourseBundle
from libqcanvas.net.canvas.page_with_content import PageWithContent
from libqcanvas.net.constants import SYNC_GOAL
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import CompoundTaskReporter

_logger = logging.getLogger(__name__)


class CanvasPageLoader:
    def __init__(self, canvas_client: CanvasClient):
        self._canvas_client = canvas_client

    async def prepare_pages_for_update(
        self,
        session: AsyncSession,
        course_bundles: list[CourseBundle],
        last_update_time: datetime,
    ) -> list[PageWithContent]:
        pages = []

        for bundle in course_bundles:
            for module in bundle.modules:
                for position, module_item in enumerate(module.module_items):
                    if isinstance(module_item.content, gql.Page):
                        content = module_item.content
                        existing_page = await session.get(db.Page, content.q_id)
                        add_page = False

                        if existing_page is None:
                            # The page doesn't exist in our version of the database
                            add_page = True
                        elif not existing_page.can_view:
                            # The page is locked in our version of the database
                            add_page = True
                        elif self._is_module_item_out_of_date(
                            last_update_time, module_item
                        ):
                            add_page = True

                        if add_page:
                            _logger.debug(
                                "Preparing page %s (id=%s) for loading",
                                content.title,
                                content.q_id,
                            )
                            pages.append(
                                self._convert_to_page_with_content(
                                    page=module_item.content,
                                    module=module,
                                    course=bundle.course,
                                    position=position,
                                )
                            )
                        else:
                            _logger.debug(
                                "Discarding page %s (id=%s)",
                                content.title,
                                content.q_id,
                            )

        return pages

    async def load_pages_in_place(self, pages: list[PageWithContent]) -> None:
        if not pages:
            return

        with register_reporter(
            CompoundTaskReporter(SYNC_GOAL, "Load pages", len(pages))
        ) as prog:
            async with TaskGroup() as tg:
                for page in pages:
                    prog.attach(tg.create_task(self._load_page_content_inplace(page)))

    @staticmethod
    def _is_module_item_out_of_date(
        last_update_time: datetime, module_item: ModuleItem
    ) -> bool:
        return module_item.content.updated_at >= last_update_time

    @staticmethod
    def _convert_to_page_with_content(
        page: Page, module: Module, course: ShallowCourse, position: int
    ):
        return PageWithContent(
            q_id=page.q_id,
            name=page.title,
            updated_at=page.updated_at,
            created_at=page.created_at,
            module=module,
            course=course,
            position=position,
        )

    async def _load_page_content_inplace(self, page: PageWithContent):
        result = await self._canvas_client.get_page(
            page_id=page.q_id, course_id=page.course.q_id
        )
        _logger.debug('Loaded page %s (id="%s")', page.name, page.q_id)

        page.is_locked = result.locked_for_user
        page.content = result.body

        if result.lock_info is not None:
            page.unlock_at = result.lock_info.unlock_at
            page.lock_at = result.lock_info.lock_at
