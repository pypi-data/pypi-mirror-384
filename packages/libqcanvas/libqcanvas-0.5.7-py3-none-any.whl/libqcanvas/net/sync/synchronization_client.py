import asyncio
import logging
from datetime import datetime
from pathlib import Path

from aiofile import async_open
from libqcanvas_clients.canvas import Announcement, CanvasClient
from libqcanvas_clients.panopto import PanoptoClient
from pydantic import ValidationError

from libqcanvas.database import QCanvasDatabase
from libqcanvas.net.canvas import CanvasDataAggregator, CanvasPageLoader, CourseMailItem
from libqcanvas.net.canvas.course_bundle import CourseBundle
from libqcanvas.net.constants import SYNC_GOAL
from libqcanvas.net.panopto.panopto_data_aggregator import PanoptoDataAggregator
from libqcanvas.net.resources.scanning.resource_linker import ResourceLinker
from libqcanvas.net.resources.scanning.resource_scanner import ResourceScanner
from libqcanvas.net.sync._canvas_data_bundle import CanvasDataBundle
from libqcanvas.net.sync._new_content_collector import NewContentCollector
from libqcanvas.net.sync._sync_meta import SyncMeta
from libqcanvas.net.sync.api_data_importer import APIDataImporter
from libqcanvas.net.sync.data_adapter import DataAdapter
from libqcanvas.net.sync.sync_receipt import SyncReceipt
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import AtomicTaskReporter, CompoundTaskReporter
from libqcanvas.util import CollectingTaskGroup, flatten

_logger = logging.getLogger(__name__)


class SynchronizationClient:
    """
    A SynchronizationClient uses a CanvasClient to retrieve data from canvas and a ResourceScanner to extract resources
    from each course. This data is added to the QCanvasDatabase.
    """

    def __init__(
        self,
        database: QCanvasDatabase,
        canvas_client: CanvasClient,
        panopto_client: PanoptoClient,
        resource_scanner: ResourceScanner,
        sync_meta_store_location: Path,
    ):
        self._database = database
        self._canvas_client = canvas_client
        self._canvas_data_aggregator = CanvasDataAggregator(
            canvas_client=self._canvas_client
        )
        self._panopto_data_aggregator = PanoptoDataAggregator(
            panopto_client=panopto_client
        )
        self._sync_meta_store_location = sync_meta_store_location
        self._sync_meta: SyncMeta | None = None
        self._canvas_page_loader = CanvasPageLoader(canvas_client=self._canvas_client)
        self._resource_scanner = resource_scanner

    async def synchronise_canvas(
        self, include_old_courses: bool = False
    ) -> SyncReceipt:
        await self._read_sync_meta()

        receipt = SyncReceipt()
        new_content_tracker = NewContentCollector()
        sync_observers = [receipt, new_content_tracker]

        with register_reporter(AtomicTaskReporter(SYNC_GOAL, "Fetch user information")):
            user_id = await self._canvas_client.get_current_user_id()

        canvas_sync_data = await self._fetch_remote_sync_data(
            user_id, include_old_courses=include_old_courses
        )

        async with self._database.session() as session:
            importer = APIDataImporter(session)
            resource_linker = ResourceLinker(session)
            adapter = DataAdapter(importer)

            importer.observers.extend(sync_observers)
            resource_linker.observers.extend(sync_observers)

            await adapter.convert_and_add_to_database(canvas_sync_data)

            scanned_resources = await self._resource_scanner.scan_content_for_resources(
                new_content_tracker.new_content
            )
            with register_reporter(AtomicTaskReporter(SYNC_GOAL, "Link resources")):
                await resource_linker.link_resources(scanned_resources)

        await self._update_sync_meta()

        _logger.info("Sync finished")
        _logger.debug(receipt)

        return receipt.finalise()

    async def _read_sync_meta(self):
        if self._sync_meta is None:
            if self._sync_meta_store_location.exists():
                try:
                    async with async_open(self._sync_meta_store_location, "r") as file:
                        self._sync_meta = SyncMeta.model_validate_json(
                            await file.read()
                        )
                except ValidationError:
                    _logger.warning("Sync metadata json file was invalid! Ignoring it")
                    self._sync_meta = SyncMeta()
            else:
                self._sync_meta = SyncMeta()

    async def _update_sync_meta(self):
        self._sync_meta.last_sync_time = datetime.now().astimezone()
        async with async_open(self._sync_meta_store_location, "w") as file:
            await file.write(self._sync_meta.model_dump_json())

    async def _fetch_remote_sync_data(
        self, user_id: str, include_old_courses: bool
    ) -> CanvasDataBundle:
        _logger.info("Last sync time is %s", self._sync_meta.last_sync_time)

        course_bundles = await self._canvas_data_aggregator.pull_courses(
            await self._database.get_existing_course_ids(),
            include_old_courses=not include_old_courses,
        )

        async with self._database.session() as session:
            pages = await self._canvas_page_loader.prepare_pages_for_update(
                session=session,
                course_bundles=course_bundles,
                last_update_time=self._sync_meta.last_sync_time,
            )

        mail: list[CourseMailItem] = []
        announcements: list[Announcement] = []
        course_panopto_folders: dict[str, str] = {}

        async def get_mail() -> None:
            nonlocal mail
            nonlocal user_id
            mail = await self._canvas_data_aggregator.get_all_course_mail(user_id)

        async def get_announcements() -> None:
            nonlocal announcements
            nonlocal course_bundles
            announcements = flatten(
                await self._get_announcements_for_courses(course_bundles)
            )

        async def load_pages() -> None:
            nonlocal pages
            await self._canvas_page_loader.load_pages_in_place(pages)

        # async def get_panopto_folders():
        #     nonlocal course_panopto_folders
        #     nonlocal courses
        #     course_panopto_folders = (
        #         await self._panopto_data_aggregator.get_course_panopto_folders(courses)
        #     )

        async def dummy_panopto_task() -> None:
            """
            Run a panopto request so that the client authenticates itself.
            This should prevent the resource scan from pausing partway through (and confusing the user) due to needing to authenticate.
            """

            # Currently unused!

            with register_reporter(
                AtomicTaskReporter(SYNC_GOAL, "Panopto authentication")
            ):
                await self._panopto_data_aggregator.get_folders()

        await asyncio.gather(get_mail(), get_announcements(), load_pages())

        _logger.info(
            "%i courses, %i pages, %i mails, and %i announcements pulled from canvas",
            len(course_bundles),
            len(pages),
            len(mail),
            len(announcements),
        )

        return CanvasDataBundle(
            courses=course_bundles,
            pages=pages,
            messages=mail + announcements,
            course_panopto_folders=course_panopto_folders,
        )

    async def _get_announcements_for_courses(
        self, course_bundles: list[CourseBundle]
    ) -> list[list[Announcement]]:
        _logger.info("Fetching announcements for %i courses", len(course_bundles))

        if len(course_bundles) == 0:
            return []

        with register_reporter(
            CompoundTaskReporter(SYNC_GOAL, "Fetch announcements", len(course_bundles))
        ) as prog:
            async with CollectingTaskGroup[list[Announcement]]() as tg:
                for bundle in course_bundles:
                    prog.attach(
                        tg.create_task(
                            self._canvas_client.get_announcements(bundle.course.q_id)
                        )
                    )

        return tg.results
